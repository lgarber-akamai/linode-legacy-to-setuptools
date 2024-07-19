# Legacy To TechDocs

A simple CLI tool to convert legacy Linode API docs links to TechDocs links, and apply them across a set of files.

For example:

```
https://www.linode.com/docs/api/domains/#domain-record-view
```

would be replaced with:

```
https://techdocs.akamai.com/linode-api/reference/get-domain-record
```

## Usage

```
usage: linode-docs-translator [-h] {bake,convert,replace} ...

Translate legacy linode.com/docs URLs to TechDocs URLs

options:
  -h, --help            show this help message and exit

subcommand:
  {bake,convert,replace}
    bake                Bake the legacy and new OpenAPI specs for faster runtime execution.
    convert             Convert the given API docs URL to a TechDocs URL.
    replace             Replace all occurrences of an API docs URL in a file with their TechDocs counterparts and print the results.
```

### Installation

#### From Git

```bash
pip install --upgrade git@github.com:lgarber-akamai/linode-legacy-to-techdocs.git
```

#### From Local Project

```bash
make install
```

### Samples

#### Convert a single API URL

```bash
legacy-to-techdocs convert "https://www.linode.com/docs/api/linode-types/#type-view"
```

#### Convert and write changes to a single file containing multiple API URLs

```bash
legacy-to-techdocs replace -w my-file.md
```

### Convert and write changes to all Python files in a directory

```bash
find ./my-dir -type f -name '*.py' | xargs legacy-to-techdocs replace -w -f
```
