
Cut a Release
=============

Create a PR to the `main` branch and go through the following steps:

**Preparation**
- Bump version in `rsciio/version.py`
- Update and check changelog in `CHANGES.rst`: run `towncrier build` (to preview, run `towncrier build --draft`)
- (optional) check conda-forge and wheels build. Pushing a tag to a fork will run the release workflow. It will not upload to pypi, because it is only enabled from the `hyperspy` organisation
- Let that PR collect comments for a day to ensure that other maintainers are comfortable with releasing

**Tag and release**
:warning: this is a point of no return :warning:
- push tag (`vx.y.z`) to the upstream repository and the following will be triggered:
  - build of the wheels and sdist and their upload to pypi
  - update of the current `stable` version on readthedocs to this tag
  - creation of a Github Release
  - creation of a zenodo record and the mining of a DOI (triggered by a new release)

**Post-release action**
- Increment the version and set it back to dev: `vx.y.z.dev0`
- Update version in other branches when necessary
- Merge the PR

Follow-up
=========

- Tidy up and close corresponding milestone
- A PR to the conda-forge feedstock will be created by the conda-forge bot

Additional information
======================
- In case a release workflow fails, it is possible to force push a tag (after fixing the workflow is necessary).
- It is best practise to avoid deleting/adding packages to pypi and use this workflow instead. On pypi, packages can be deleted but can't be updated - when a package is deleted, it will not be possible to upload one with the same name.
- Zenodo entry can't be removed. As the Zenodo entry is created on the GitHub release creating, it is best to create the release as the last step, to avoid creating uncessary Zenodo entry when for example, the release workflow fails.
