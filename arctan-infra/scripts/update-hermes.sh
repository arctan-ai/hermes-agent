#!/bin/bash
# Update Hermes from upstream NousResearch and rebase Arctan customizations
set -e

cd ~/.hermes/hermes-agent

echo "Fetching upstream..."
git fetch upstream

echo "Updating main..."
git checkout main
git merge upstream/main

echo "Rebasing arctan/production..."
git checkout arctan/production
git rebase main

echo "Pushing to fork..."
git push origin arctan/production --force-with-lease
git push origin main

echo "Restarting gateway..."
hermes gateway restart

echo "Done! Hermes updated and restarted."
