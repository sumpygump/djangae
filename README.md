# Djangae

![Pipeline status](https://gitlab.com/potato-oss/djangae/djangae/badges/master/pipeline.svg)

The best way to run Django on Google Cloud.

Djangae (djan-gee) is a Django app that allows you to run Django applications on the Google Cloud platform, including (if you
want to) using Django's models with Google Cloud Datastore as the underlying database.

:earth_africa:&nbsp;&nbsp;[Website](https://djangae.org)&nbsp;&nbsp;|&nbsp;&nbsp;
:computer:&nbsp;&nbsp;[GitLab](https://gitlab.com/potato-oss/djangae/djangae)&nbsp;&nbsp;|&nbsp;&nbsp;
:closed_book:&nbsp;&nbsp; [Docs](https://djangae.readthedocs.io/)&nbsp;&nbsp;|&nbsp;&nbsp;
:busts_in_silhouette:&nbsp;&nbsp;[Google Group](https://groups.google.com/forum/#!forum/djangae-users)

---

## Looking for Commercial Support?

Potato offers Commercial Support for all its Open Source projects and we can tailor a support package to your needs.

If you're interested in commercial support, training, or consultancy then go ahead and contact us at [opensource@potatolondon.com](mailto:opensource@potatolondon.com)

---


**Note: Djangae is under heavy development, stability is not guaranteed. A 2.0 release will happen when it's ready. If you are using Django 1.11 / Python 2.7, please use the 1.x branch which is stable**

## Features

* Hooks to manage a series of Google Cloud emulators to simulate the Google App Engine environment locally
* A tasks app which implements "deferred" tasks on Google Cloud Tasks, and functions for iterating large datasets
* Utility functions to discover information about the running environment
* A series of security patches and checks to improve the security of your project
* Test utils for testing code that uses the Cloud Tasks API
* Apps for cross-request locking and efficient pagination on the Google Cloud Datastore

## Supported Django Versions

Djangae currently supports Django 2.2.

## Documentation

[https://djangae.readthedocs.io/](https://djangae.readthedocs.io/)

# Installation

See [https://djangae.readthedocs.io/en/latest/installation/](https://djangae.readthedocs.io/en/latest/installation/)


# Contributing to Djangae

Djangae is actively developed and maintained, so if you're thinking of contributing to the codebase, here is how to get started.

## Get started with development

1. First off, head to [our GitLab page](https://gitlab.com/potato-oss/djangae/djangae) and fork the repository to have your own copy of it.
2. Clone it locally to start setting up your development environment
3. Run all tests to make sure your local version is working: `tox -e py37`

## Pick an issue & send a Merge Request

If you spotted a bug in Djangae that you want to fix, it's a good idea to start
off by [adding an issue](https://gitlab.com/potato-oss/djangae/djangae/-/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=).
This will allow us to verify that your issue is valid, and suggest ideas for fixing it, so
no time is wasted for you.

For help with creating the merge request, check out [GitLab documentation](https://docs.gitlab.com/ee/user/project/merge_requests/).

## Code style

Code style should follow PEP-8 with a line length of 100 characters.

## Need help?

Reach out to us on [djangae-users](https://groups.google.com/forum/#!forum/djangae-users) mailing list.

## Merge request requirements

For merge request to be merged, following requirements should be met:

- Tests covering new or changed code are added or updated
- Relevant documentation should be updated or added
- Line item should be added to CHANGELOG.md, unless change is really irrelevant

# Running tests

On setting up the first time, create a Python 3 virtualenv and install the prerequisites with

```
# install tox
pip install tox

# install the datastore emulator
gcloud components install cloud-datastore-emulator
```

If you don't have `gcloud` (the Google Cloud SDK) installed, installation instructions can be found [here](https://cloud.google.com/sdk/install)

For running the tests, you just need to run:

    $ tox -e py37


You can run specific tests in the usual way by doing:

    tox -e py37 -- some_app.SomeTestCase.some_test_method
