# djangae.contrib.secrets

It's generally bad practice to store secrets in your code, as in the event that the code leaks your site and data could be compromised. `djangae.contrib.secrets` provides a mechanism to store your project's secrets in various locations outside of the project code itself. The motivation for including this app with Djangae is secure storage of the Django `SECRET_KEY` value.

## Backends

The secrets app provides a few backends for storing your secrets:

 - Google Secret Manager - stores your secrets in Google Secrets Manager
 - Google Cloud Datastore - stores your secrets in a Cloud Datastore entities. This uses the raw Google Cloud Datastore API rather than Django models due to the requirement of allowing access to secrets from a Django settings file.
 - Filesystem - stores your secrets in a **plain-text file**

## Google Secret Manager

The GSM storage backend stores your secrets in a single JSON object in a single GSM secret. The backend takes two required arguments:

 - `project_id` - this is the GCP project ID for the GSM service
 - `secret_id` - this is the name of the secret used to store the JSON object

## Google Cloud Datastore

The Google Cloud Datastore backend stores your secrets in a singleton datastore entity. The required arguments are:

 - `kind_name` - the kind of the entity
 - `key_name` - the ID of the entity. This can be an integer or string.
 - `namespace` - optional namespace for the entity key
 - `project_id` - optional project ID for the client connection

## Filesystem

The filesystem backend has a single required argument:

 - `filename` - the filename of the JSON file containing the secrets dictionary

## Example Usage

You can access secrets using `djangae.contrib.secrets.get` and passing an appropriate backend instance:

```
MySecrets = secrets.get(
    backend=secrets.FilesystemBackend(filename=filename)
)

print(MySecrets.secret_key)
```
