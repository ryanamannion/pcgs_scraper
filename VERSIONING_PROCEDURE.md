# Versioning
```
# Remove "-dev" from version in pcgs_scraper/__init__.py
git diff
python setup.py sdist
# Test install in environment w/o requirements
pip list
pip install dist/pcgs_scraper-*.*.*.tar.gz
# install successful
git add dist/pcgs_scraper-*.*.*.tar.gz
git status
git add .
git commit -m "commit for version X.Y.Z"
git tag -a vX.Y.Z -m "commit for version X.Y.Z"
# Iterate the version to "X.Y.Z+1-dev" in pcgs_scraper/__init__.py 
# add a new header in the CHANGELOG
git add pcgs_scraper/__init__.py CHANGELOG
git status
git commit -m "Start of dev for version X.Y.Z+1"

git push
git push --tags
# Go on to github and edit the pushed tag. Paste the CHANGELOG
# in to make everyone happy. Publish the release.
```
