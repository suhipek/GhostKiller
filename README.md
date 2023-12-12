<p align="center">
  <img src="resources/icon.jpeg" alt="icon" width="100" height="100" align="center"/>
</p>

<h1 align="center">GhostKiller</h1>

<div align="center">
  
  Track how much time your recipant spend on reading your mail
  
  NKU Database System 2023 Spring Course Project
  
</div>

## How it works

An invisible 1*1 size image is embedded in the email, and the image URL points to a controlled server.

For trackers that need to view user retention time, the request for the image URL will return a 302 redirect after a certain time, with the redirection target still on the controlled server. After multiple redirects, we can determine the retention time by comparing the time of the first visit and the last visit.
