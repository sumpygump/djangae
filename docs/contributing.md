# Contributing to Djangae

Djangae is actively developed and maintained, so if you're thinking of contributing to the codebase, here is how to get started.

## Get started with development

1. First off, head to [our GitLab page](https://gitlab.com/potato-oss/djangae/djangae) and fork the repository to have your own copy of it.
2. Clone it locally to start setting up your development environment
3. Run all tests to make sure your local version is working (see instructions in README.md).

## Pick an issue & send a merge request

If you spotted a bug in Djangae that you want to fix, it's a good idea to start
off by [adding an issue](https://gitlab.com/potato-oss/djangae/djangae/-/issues/new).
This will allow us to verify that your issue is valid, and suggest ideas for fixing it, so
no time is wasted for you.

For help with creating the merge request, check out [GitLab documentation](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html).

## Code style

Code style should follow PEP-8 with a loose line length of 100 characters.

## Need help?

Reach out to us on [djangae-users](https://groups.google.com/forum/#!forum/djangae-users) mailing list.

## Merge request requirements

For pull request to be merged, following requirements should be met:

- Tests covering new or changed code are added or updated
- Relevant documentation should be updated or added
- Line item should be added to CHANGELOG.md, unless change is really irrelevant


## Running tests

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
