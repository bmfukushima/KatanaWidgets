# Isolate CEL
The Isolate CEL node adds CEL functionality to a standard Isolate Node.
The Isolate node has never supported CEL due to performance issues, however
technology has evolved slightly over the past 20 years, and the Isolate CEL
may be a viable option now.

# How it works
The user will input the standard parameters that an `Isolate` node takes.  With the CEL
being the locations to keep, and the parameter `isolateFrom` being the location
that the CEL locations will be isolated from (see note for inverted outputs).

Under the hood, this will assign a **custom attribute** to all of the locations
selected.  It will then **resolve** these locations, and give that **custom attribute**
to all of the found locations parent locations.  Finally, it will **prune**
all of the locations that don't have this attribute with an OpScript.

### Note
**Inverted output currently does not honor the `isolateFrom` param**