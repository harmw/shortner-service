# URL shortner
A REST service to deliver tiny urls, using a Redis store for persistence.

# Design Goals
When storing urls to the REST service, the following principles have been applied:
* short urls have just one long url
* short urls are permanently stored and persisted using a sqlite database
* short urls are unique from one another
* short urls are not easily discoverable; low probability of finding urls based in incrementing urls

When retrieving information from the REST service:
* the service will send a standard redirect to the longurl
* the service will send a response within 10ms
* the service keeps track of such events
* the service can show hits per shorturl per minute/24h/week/alltime

Clients can store new urls using a simple `POST`. The service will get the next available _id_ from the Redis store and use that for storing the url. This _id_ will be returned using `base32(id)`.

# Building
Using docker:
`docker build -t shortner:1.0 .`

# Running
Using docker to first start Redis:

`docker run --rm -it -v /tmp/redis:/data -p 6379:6379 redis:3.2.8`

Launch the shortner:

`docker run --rm -it -e LOG_LEVEL=INFO -e REDIS_HOST=172.17.0.2 -v /tmp:/work -p 8080:8080 shortner:1.0`

# Using
Adding a new url to the service:
```
curl -d '{"url": "https://google.com/?foobar"}' -H 'content-type: application/json' http://localhost:8080/add
```

Response:
```
{
  "result": "added",
  "shorturlid": "a",
  "url": "https://google.com/?foobar"
}
```

Using the short url to redirect to the long url:
```
curl localhost:8080/u/a
```

Response:
```
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to target URL: <a href="https://google.com/?foobar">https://google.com/?foobar</a>.  If not click the link.
```

# Future work
 [ ] Implement something like Swagger
