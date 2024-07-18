# Legacy To TechDocs API URL Utility

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

### Requirements

Install Python requirements:

```python
pip install pyyaml openapi3
```

Download OpenAPI specs:

```
# Download new spec
curl https://.../openapi.yaml -o openapi.yaml

# Download old spec
curl https://raw.githubusercontent.com/linode/linode-api-docs/development/openapi.yaml -o openapi-legacy.yaml
```

### Samples

#### Convert a single API URL

```bash
python3 legacy_to_techdocs.py convert "https://www.linode.com/docs/api/linode-types/#type-view"
```

#### Convert and write changes to a single file containing multiple API URLs

```bash
python3 legacy_to_techdocs.py replace -w my-file.md
```

#### Convert and write changes to a directory of multiple files

```bash
python3 legacy_to_techdocs.py replace -w -r my-directory
```

### Convert and write changes to a directory of multiple files filtering by extension

```bash
find ./my-dir -type f -name '*.py' | xargs python3 legacy_to_techdocs.py replace -w -f
```
