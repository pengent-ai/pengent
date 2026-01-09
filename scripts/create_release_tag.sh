#!/bin/sh

# リリースのバージョンを引数にする
VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Error: Version argument is required."
  echo "Usage: $0 <version>"
  exit 1
fi

git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin "v$VERSION"