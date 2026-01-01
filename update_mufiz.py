#!/usr/bin/env python3
"""
Auto-updater script for MufiZ.json
Fetches the latest release from GitHub and updates the Scoop manifest with new hashes and URLs.
"""

import hashlib
import json
import os
import sys
from typing import Any, Dict, Optional

import requests

# Configuration
GITHUB_REPO = "Mufi-Lang/MufiZ"
MANIFEST_PATH = "bucket/MufiZ.json"
USER_AGENT = "MufiZ-Bucket-Updater/1.0"

# Architecture mappings
ARCH_MAPPINGS = {
    "x86_64-windows": "64bit",
    "x86-windows-gnu": "32bit",
    "aarch64-windows": "arm64",
}


class MufiZUpdater:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Fetch the latest release information from GitHub API."""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching latest release: {e}")
            return None

    def download_and_hash(self, url: str) -> Optional[str]:
        """Download a file and return its SHA256 hash."""
        try:
            print(f"Downloading {url}...")
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            sha256_hash = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=8192):
                sha256_hash.update(chunk)

            return sha256_hash.hexdigest()
        except requests.RequestException as e:
            print(f"Error downloading {url}: {e}")
            return None

    def load_manifest(self) -> Optional[Dict[str, Any]]:
        """Load the existing MufiZ.json manifest."""
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading manifest: {e}")
            return None

    def save_manifest(self, manifest: Dict[str, Any]) -> bool:
        """Save the updated manifest back to MufiZ.json."""
        try:
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving manifest: {e}")
            return False

    def find_asset_urls(self, release: Dict[str, Any], version: str) -> Dict[str, str]:
        """Find download URLs for each architecture from release assets."""
        urls = {}

        for asset in release.get("assets", []):
            asset_name = asset["name"]
            download_url = asset["browser_download_url"]

            # Match asset names to architectures
            for arch_key, scoop_arch in ARCH_MAPPINGS.items():
                if arch_key in asset_name and asset_name.endswith(".zip"):
                    urls[scoop_arch] = download_url
                    break

        return urls

    def update_manifest(self) -> bool:
        """Main update logic."""
        print("Fetching latest release information...")
        release = self.get_latest_release()
        if not release:
            return False

        version = release["tag_name"].lstrip("v")
        print(f"Latest version: {version}")

        print("Loading current manifest...")
        manifest = self.load_manifest()
        if not manifest:
            return False

        current_version = manifest.get("version", "unknown")
        print(f"Current version: {current_version}")

        if version == current_version:
            print("Manifest is already up to date!")
            return True

        print(f"Updating from version {current_version} to {version}")

        # Find asset URLs
        asset_urls = self.find_asset_urls(release, version)
        if len(asset_urls) != 3:
            print(f"Warning: Expected 3 assets, found {len(asset_urls)}")
            print(f"Found assets: {list(asset_urls.keys())}")

        # Update architecture section
        updated_archs = {}
        for arch, url in asset_urls.items():
            print(f"Processing {arch} architecture...")
            hash_value = self.download_and_hash(url)
            if hash_value:
                updated_archs[arch] = {"url": url, "hash": hash_value}
                print(f"  ✓ {arch}: {hash_value}")
            else:
                print(f"  ✗ Failed to process {arch}")
                return False

        # Update manifest
        manifest["version"] = version
        manifest["architecture"] = updated_archs

        # Save updated manifest
        if self.dry_run:
            print("\n--- DRY RUN MODE ---")
            print("Would update manifest with:")
            print(
                json.dumps(
                    {"version": version, "architecture": updated_archs}, indent=2
                )
            )
            print(f"✓ Dry run completed - would update MufiZ.json to version {version}")
            return True
        else:
            print("Saving updated manifest...")
            if self.save_manifest(manifest):
                print(f"✓ Successfully updated MufiZ.json to version {version}")
                return True
            else:
                print("✗ Failed to save manifest")
                return False


def main():
    """Main entry point."""
    # Check for dry run mode
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest file {MANIFEST_PATH} not found!")
        print("Please run this script from the root of the mufi-bucket repository.")
        sys.exit(1)

    if dry_run:
        print("Running in DRY RUN mode - no files will be modified")

    updater = MufiZUpdater(dry_run=dry_run)
    success = updater.update_manifest()

    if success:
        if dry_run:
            print("\n🎉 Dry run completed successfully!")
        else:
            print("\n🎉 Update completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Update failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
