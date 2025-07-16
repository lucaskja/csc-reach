#!/usr/bin/env python3
"""
Build Cache Manager for CSC-Reach
Implements intelligent caching to speed up builds and reduce redundant work.
"""

import os
import sys
import json
import hashlib
import shutil
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import subprocess


class BuildCacheManager:
    """Manages build caching for faster execution."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cache_dir = project_root / 'build' / 'cache'
        self.cache_index_file = self.cache_dir / 'cache_index.json'
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.cache_config = {
            'max_age_days': 30,
            'max_cache_size_mb': 2048,  # 2GB max cache
            'compression_enabled': True,
            'cache_types': {
                'dependencies': {
                    'enabled': True,
                    'max_age_days': 7,
                    'sources': ['requirements.txt', 'pyproject.toml', 'setup.py']
                },
                'pyinstaller': {
                    'enabled': True,
                    'max_age_days': 14,
                    'sources': ['src/**/*.py', 'scripts/build/*.spec']
                },
                'build_artifacts': {
                    'enabled': True,
                    'max_age_days': 3,
                    'sources': ['src/**/*.py', 'config/**', 'assets/**']
                },
                'test_results': {
                    'enabled': True,
                    'max_age_days': 1,
                    'sources': ['tests/**/*.py', 'src/**/*.py']
                }
            }
        }
        
        # Load cache index
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict:
        """Load the cache index from disk."""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading cache index: {e}")
        
        return {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'entries': {},
            'statistics': {
                'total_entries': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'total_size_bytes': 0
            }
        }
    
    def _save_cache_index(self):
        """Save the cache index to disk."""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving cache index: {e}")
    
    def _calculate_content_hash(self, sources: List[str]) -> str:
        """Calculate hash of source files/patterns."""
        hasher = hashlib.sha256()
        
        for source_pattern in sources:
            # Handle glob patterns
            if '**' in source_pattern or '*' in source_pattern:
                from glob import glob
                files = glob(str(self.project_root / source_pattern), recursive=True)
                files.sort()  # Ensure consistent ordering
            else:
                source_path = self.project_root / source_pattern
                files = [str(source_path)] if source_path.exists() else []
            
            for file_path in files:
                file_path = Path(file_path)
                if file_path.is_file():
                    try:
                        # Include file path and modification time in hash
                        hasher.update(str(file_path.relative_to(self.project_root)).encode())
                        hasher.update(str(file_path.stat().st_mtime).encode())
                        
                        # For small files, include content
                        if file_path.stat().st_size < 1024 * 1024:  # 1MB
                            with open(file_path, 'rb') as f:
                                hasher.update(f.read())
                    except Exception as e:
                        print(f"⚠️ Error hashing {file_path}: {e}")
        
        return hasher.hexdigest()
    
    def _get_cache_key(self, cache_type: str, additional_context: Optional[Dict] = None) -> str:
        """Generate a cache key for the given type and context."""
        if cache_type not in self.cache_config['cache_types']:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        config = self.cache_config['cache_types'][cache_type]
        content_hash = self._calculate_content_hash(config['sources'])
        
        # Include additional context in the key
        context_str = ""
        if additional_context:
            context_str = json.dumps(additional_context, sort_keys=True)
        
        # Combine cache type, content hash, and context
        key_data = f"{cache_type}:{content_hash}:{context_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file system path for a cache key."""
        # Use first 2 chars as subdirectory for better file system performance
        subdir = cache_key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{cache_key}.cache"
    
    def is_cache_valid(self, cache_type: str, additional_context: Optional[Dict] = None) -> bool:
        """Check if cache entry is valid and not expired."""
        if not self.cache_config['cache_types'][cache_type]['enabled']:
            return False
        
        cache_key = self._get_cache_key(cache_type, additional_context)
        
        if cache_key not in self.cache_index['entries']:
            return False
        
        entry = self.cache_index['entries'][cache_key]
        cache_path = self._get_cache_path(cache_key)
        
        # Check if cache file exists
        if not cache_path.exists():
            # Remove stale index entry
            del self.cache_index['entries'][cache_key]
            self._save_cache_index()
            return False
        
        # Check expiration
        max_age = self.cache_config['cache_types'][cache_type]['max_age_days']
        created_time = datetime.fromisoformat(entry['created'])
        if datetime.now() - created_time > timedelta(days=max_age):
            self._remove_cache_entry(cache_key)
            return False
        
        return True
    
    def get_from_cache(self, cache_type: str, additional_context: Optional[Dict] = None) -> Optional[Any]:
        """Retrieve data from cache."""
        if not self.is_cache_valid(cache_type, additional_context):
            self.cache_index['statistics']['cache_misses'] += 1
            self._save_cache_index()
            return None
        
        cache_key = self._get_cache_key(cache_type, additional_context)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # Update access time
            self.cache_index['entries'][cache_key]['last_accessed'] = datetime.now().isoformat()
            self.cache_index['statistics']['cache_hits'] += 1
            self._save_cache_index()
            
            print(f"✅ Cache hit for {cache_type}")
            return data
            
        except Exception as e:
            print(f"⚠️ Error reading cache {cache_key}: {e}")
            self._remove_cache_entry(cache_key)
            self.cache_index['statistics']['cache_misses'] += 1
            self._save_cache_index()
            return None
    
    def store_in_cache(self, cache_type: str, data: Any, additional_context: Optional[Dict] = None):
        """Store data in cache."""
        if not self.cache_config['cache_types'][cache_type]['enabled']:
            return
        
        cache_key = self._get_cache_key(cache_type, additional_context)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Update index
            file_size = cache_path.stat().st_size
            self.cache_index['entries'][cache_key] = {
                'type': cache_type,
                'created': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'size_bytes': file_size,
                'context': additional_context or {}
            }
            
            self.cache_index['statistics']['total_entries'] = len(self.cache_index['entries'])
            self.cache_index['statistics']['total_size_bytes'] += file_size
            
            self._save_cache_index()
            print(f"💾 Cached {cache_type} ({file_size / 1024:.1f} KB)")
            
            # Check if we need to clean up old entries
            self._cleanup_if_needed()
            
        except Exception as e:
            print(f"⚠️ Error storing cache {cache_key}: {e}")
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove a cache entry."""
        if cache_key in self.cache_index['entries']:
            cache_path = self._get_cache_path(cache_key)
            
            # Remove file
            if cache_path.exists():
                try:
                    file_size = cache_path.stat().st_size
                    cache_path.unlink()
                    self.cache_index['statistics']['total_size_bytes'] -= file_size
                except Exception as e:
                    print(f"⚠️ Error removing cache file {cache_path}: {e}")
            
            # Remove from index
            del self.cache_index['entries'][cache_key]
            self.cache_index['statistics']['total_entries'] = len(self.cache_index['entries'])
    
    def _cleanup_if_needed(self):
        """Clean up cache if it's too large or has too many old entries."""
        current_size_mb = self.cache_index['statistics']['total_size_bytes'] / (1024 * 1024)
        
        if current_size_mb > self.cache_config['max_cache_size_mb']:
            print(f"🧹 Cache size ({current_size_mb:.1f} MB) exceeds limit, cleaning up...")
            self.cleanup_cache(target_size_mb=self.cache_config['max_cache_size_mb'] * 0.8)
    
    def cleanup_cache(self, target_size_mb: Optional[float] = None, max_age_days: Optional[int] = None):
        """Clean up cache entries."""
        if max_age_days is None:
            max_age_days = self.cache_config['max_age_days']
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        removed_size = 0
        
        # Remove expired entries
        expired_keys = []
        for cache_key, entry in self.cache_index['entries'].items():
            created_time = datetime.fromisoformat(entry['created'])
            if created_time < cutoff_time:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            entry = self.cache_index['entries'][cache_key]
            removed_size += entry['size_bytes']
            self._remove_cache_entry(cache_key)
            removed_count += 1
        
        # If we still need to reduce size, remove least recently used entries
        if target_size_mb:
            current_size_mb = self.cache_index['statistics']['total_size_bytes'] / (1024 * 1024)
            
            if current_size_mb > target_size_mb:
                # Sort by last accessed time (oldest first)
                entries_by_access = sorted(
                    self.cache_index['entries'].items(),
                    key=lambda x: x[1]['last_accessed']
                )
                
                for cache_key, entry in entries_by_access:
                    if current_size_mb <= target_size_mb:
                        break
                    
                    removed_size += entry['size_bytes']
                    current_size_mb -= entry['size_bytes'] / (1024 * 1024)
                    self._remove_cache_entry(cache_key)
                    removed_count += 1
        
        self._save_cache_index()
        
        if removed_count > 0:
            print(f"🗑️ Removed {removed_count} cache entries ({removed_size / (1024 * 1024):.1f} MB)")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        stats = self.cache_index['statistics'].copy()
        stats['size_mb'] = stats['total_size_bytes'] / (1024 * 1024)
        
        # Calculate hit rate
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['cache_hits'] / total_requests
        else:
            stats['hit_rate'] = 0.0
        
        # Get breakdown by cache type
        type_breakdown = {}
        for entry in self.cache_index['entries'].values():
            cache_type = entry['type']
            if cache_type not in type_breakdown:
                type_breakdown[cache_type] = {'count': 0, 'size_bytes': 0}
            type_breakdown[cache_type]['count'] += 1
            type_breakdown[cache_type]['size_bytes'] += entry['size_bytes']
        
        stats['type_breakdown'] = type_breakdown
        return stats
    
    def print_cache_stats(self):
        """Print cache statistics."""
        stats = self.get_cache_stats()
        
        print("📊 Build Cache Statistics")
        print("=" * 40)
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Cache Size: {stats['size_mb']:.1f} MB")
        print(f"Hit Rate: {stats['hit_rate']:.1%}")
        print(f"Cache Hits: {stats['cache_hits']}")
        print(f"Cache Misses: {stats['cache_misses']}")
        
        if stats['type_breakdown']:
            print("\nBreakdown by Type:")
            for cache_type, info in stats['type_breakdown'].items():
                size_mb = info['size_bytes'] / (1024 * 1024)
                print(f"  {cache_type}: {info['count']} entries, {size_mb:.1f} MB")
    
    def cache_build_dependencies(self, platform: str) -> bool:
        """Cache build dependencies installation."""
        cache_key_context = {'platform': platform, 'python_version': sys.version}
        
        # Check if dependencies are cached
        cached_deps = self.get_from_cache('dependencies', cache_key_context)
        if cached_deps:
            print("✅ Using cached dependencies")
            return True
        
        # Dependencies not cached, will need to install
        print("📦 Dependencies not cached, will install fresh")
        return False
    
    def store_build_dependencies(self, platform: str, dependency_info: Dict):
        """Store build dependencies in cache."""
        cache_key_context = {'platform': platform, 'python_version': sys.version}
        self.store_in_cache('dependencies', dependency_info, cache_key_context)
    
    def cache_pyinstaller_build(self, platform: str, spec_file: str) -> Optional[Path]:
        """Check if PyInstaller build is cached."""
        cache_key_context = {
            'platform': platform,
            'spec_file': spec_file,
            'python_version': sys.version
        }
        
        cached_build = self.get_from_cache('pyinstaller', cache_key_context)
        if cached_build and isinstance(cached_build, dict):
            build_path = Path(cached_build.get('build_path', ''))
            if build_path.exists():
                print(f"✅ Using cached PyInstaller build: {build_path}")
                return build_path
        
        print("🔨 PyInstaller build not cached, will build fresh")
        return None
    
    def store_pyinstaller_build(self, platform: str, spec_file: str, build_path: Path):
        """Store PyInstaller build in cache."""
        cache_key_context = {
            'platform': platform,
            'spec_file': spec_file,
            'python_version': sys.version
        }
        
        build_info = {
            'build_path': str(build_path),
            'timestamp': datetime.now().isoformat(),
            'platform': platform
        }
        
        self.store_in_cache('pyinstaller', build_info, cache_key_context)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSC-Reach Build Cache Manager")
    parser.add_argument('action', choices=['stats', 'cleanup', 'clear'],
                       help='Action to perform')
    parser.add_argument('--max-age-days', type=int, default=30,
                       help='Maximum age for cache entries (cleanup)')
    parser.add_argument('--target-size-mb', type=float,
                       help='Target cache size in MB (cleanup)')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    cache_manager = BuildCacheManager(project_root)
    
    if args.action == 'stats':
        cache_manager.print_cache_stats()
        return 0
    
    elif args.action == 'cleanup':
        cache_manager.cleanup_cache(
            target_size_mb=args.target_size_mb,
            max_age_days=args.max_age_days
        )
        cache_manager.print_cache_stats()
        return 0
    
    elif args.action == 'clear':
        if cache_manager.cache_dir.exists():
            shutil.rmtree(cache_manager.cache_dir)
            print("🗑️ Cache cleared")
        cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())