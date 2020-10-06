# Horse / Dance

This is a library for handling file types and normalizing file names.

File types are represented as mime types with compression information. Two methods for file type detection:
1. Python's `mimetype` library, which uses just the name of the file to determine mime types.
2. The detector from `libfile`, which uses the actual file data to determine mime types.

The `MimeResolver` can be used to get and reconcile both of these methods, resulting in two mimes (if the file is available) and a `MimeResolution`, which contains both a reconciled mime (if it succeeds in reconciling the mimes) along with information about the method of reconciliation.

There is a bit more here, but this library is still being built out and does not yet have any documentation.

You can use nix to pull the relevant tools into an environment or just install them manually.
