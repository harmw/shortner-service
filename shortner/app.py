#!/usr/bin/env python
import logging
import os
import redis
import time

from flask import Flask, g, abort, jsonify, redirect, request, make_response


logging.basicConfig(level=logging.os.environ.get('LOG_LEVEL', 'DEBUG'))
# TODO: this will make guessing the next url a tiny bit harder by not using a
# logical ordering. It's still nothing special though.
charlist = '1aku2blv3cmw4dnx5eoy6fpz7gq8hr9is0jt'
base = len(charlist)
rc = redis.Redis(host=os.environ.get('REDIS_HOST', '172.17.0.2'), port=6379)
app = Flask(__name__)


def get_next_index(r):
    return r.hincrby('urls:latest', 'index', 1)


def update_counter(r, name):
    now = time.time()
    pipe = r.pipeline()
    for statscounter in [0, 60, 86400, 604800]:
        pnow = 0
        if statscounter > 0:
            pnow = int(now / statscounter) * statscounter
        hash = '%s:%s' % (statscounter, name)
        logging.debug('Updating counter %d %s, %s, current is %d' % (
            statscounter, name, hash, pnow))
        pipe.zadd('known:', hash, 0)
        pipe.hincrby('stats:count:' + hash, pnow, 1)
    pipe.execute()


def get_counter(r, url, statscounter):
    name = generate_long_url(url)
    now = time.time()
    pnow = 0
    if statscounter > 0:
        pnow = int(now / statscounter) * statscounter
    hash = '%s:%s' % (statscounter, name)
    logging.debug('Retrieving counter %d %s, %s, current is %d' % (
        statscounter, name, hash, pnow))
    data = r.hgetall('stats:count:' + hash)
    if str(pnow) in data:
        logging.debug('Returning count %s' % data[str(pnow)])
        return int(data[str(pnow)])
    return 0


def generate_short_url(urlid):
    string = ''
    logging.debug('Generating tiny url for url with id [%s]' % urlid)
    while(urlid > 0):
        string = charlist[urlid % base] + string
        urlid //= base
    return string


def generate_long_url(url):
    n = 0
    logging.debug('Generating original url for [%s]' % url)
    for char in url:
        n = n * base + charlist.index(char)
    return n


def get_hits(url, period):
    if period == '24h':
        return get_counter(rc, url, 86400)
    elif period == 'week':
        return get_counter(rc, url, 604800)
    elif period == 'alltime':
        return get_counter(rc, url, 0)
    elif period == 'minute':
        return get_counter(rc, url, 60)
    else:
        return '-1'


def get_short_url(url):
    longurlid = generate_long_url(url)
    longurl = rc.get('url.%d.longurl' % longurlid)
    if longurl is None:
        return abort(404)
    update_counter(rc, longurlid)
    logging.info("Redirecting %s to %s" % (url, longurl))
    return redirect(longurl)


def add_short_url(url):
    logging.info('Adding %s' % url)
    urlid = get_next_index(rc)
    logging.info('Next index: %s' % urlid)
    store_key = 'url.%s.longurl' % urlid
    store_val = '%s' % url
    rc.set(store_key, store_val)
    shorturl = generate_short_url(urlid)
    return jsonify({
        'result': 'added',
        'shorturlid': shorturl,
        'url': url}), 200


@app.route("/")
def home():
    return make_response(jsonify({'error': 'Nothing here'}), 404)


@app.route("/stats/<url>/access/<period>", methods=['GET'])
def get_stats(url, period):
    logging.info('Getting %s stats for %s' % (url, period))
    hits = get_hits(url, period)
    return jsonify({
        'result': 'ok',
        'hits': hits
        }), 200


@app.route("/add", methods=['POST'])
def post_add_short_url():
    if not request.json or 'url' not in request.json:
        abort(400)
    return add_short_url(request.json.get('url'))


@app.route("/u/<url>", methods=['GET'])
def handle_url(url):
    return get_short_url(url)


@app.after_request
def after_request(response):
    ms = time.time() * 1000 - g.start
    logging.info('Request took %dms' % ms)
    response.headers.add('X-Request-Milliseconds', ms)
    return response


@app.before_request
def before_request():
    g.start = time.time() * 1000


def run():
    # Set a default index so we can skip a lot shorturls using just 2 chars.
    if rc.hsetnx('urls:latest', 'index', 1001001):
        logging.info('Set urls:latest.index')
    app.run(host="0.0.0.0", port=8080, threaded=False)
