# Djangae

**Serverless Django on Google Cloud Platform**

Djangae (djan-gee) is a Django app that allows you to run serverless Django applications on Google's Cloud Platform. It provides
everything you need to write scalable Django apps using technologies like Google Cloud Datastore, Google Cloud Tasks, and Google App Engine.

Google Group: [https://groups.google.com/forum/#!forum/djangae-users](https://groups.google.com/forum/#!forum/djangae-users)

Website: [https://djangae.org](https://djangae.org)

GitLab: [https://gitlab.com/potato-oss/djangae/djangae](https://gitlab.com/potato-oss/djangae/djangae)


**Note: Djangae is under heavy development, stability is not guaranteed. A 2.0 release will happen when it's ready. If you are looking to use Djangae on Python 2, then take a look at the 1.x branch**

## Features

* Tight integration with the Django G-Cloud Connectors sibling project, which provides an ORM backend for Google Cloud Datastore
* Django authentication backends for Google OAuth and IAP
* Easy launching and management of Google Cloud emulators for local development
* Integration with Google Cloud Tasks - easily defer functions for background processing
* System checks to improve the security of your project
* Test utilities for writing tests that leverage the Google Cloud Platform (e.g. task queue processing)
* Apps for cross-request locking and efficient pagination on the Google Cloud Datastore

## Supported Django Versions

Djangae currently supports Django 3.2.
