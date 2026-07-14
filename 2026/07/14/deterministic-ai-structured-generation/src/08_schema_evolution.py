"""
Example 8: Schema Evolution

Demonstrates:
- Schema versioning
- Backward compatibility
- Migration strategies
- Shadow mode testing
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


# Version 1.0 - Original schema
class TaskV1(BaseModel):
    """Task extraction schema version 1.0"""
    
    version: Literal["1.0"] = "1.0"
    title: str = Field(min_length=5, max_length=100)
    priority: int = Field(ge=1, le=5)


# Version 2.0 - Added required category field
class TaskV2(BaseModel):
    """Task extraction schema version 2.0"""
    
    version: Literal["2.0"] = "2.0"
    title: str = Field(min_length=5, max_length=100)
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
    description: str | None = None


# Version 3.0 - Added optional fields, stricter validation
class TaskV3(BaseModel):
    """Task extraction schema version 3.0"""
    
    version: Literal["3.0"] = "3.0"
    title: str = Field(min_length=5, max_length=100)
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
    description: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=5)
    estimated_hours: float | None = Field(None, ge=0.5, le=80.0)
    created_at: datetime = Field(default_factory=datetime.now)


class SchemaMigration:
    """Handle schema migrations between versions"""
    
    @staticmethod
    def migrate_v1_to_v2(v1_data: dict) -> dict:
        """
        Migrate v1 data to v2 format
        
        v2 adds required 'category' field, so we need to infer it
        """
        v2_data = {
            "version": "2.0",
            "title": v1_data["title"],
            "priority": v1_data["priority"],
            "category": "bug",  # Default category for old data
        }
        return v2_data
    
    @staticmethod
    def migrate_v2_to_v3(v2_data: dict) -> dict:
        """
        Migrate v2 data to v3 format
        
        v3 adds optional fields, so migration is straightforward
        """
        v3_data = {
            "version": "3.0",
            "title": v2_data["title"],
            "priority": v2_data["priority"],
            "category": v2_data["category"],
            "description": v2_data.get("description"),
            "tags": [],
            "estimated_hours": None,
            "created_at": datetime.now(),
        }
        return v3_data
    
    @staticmethod
    def migrate_any_to_latest(data: dict) -> dict:
        """Migrate any version to the latest version"""
        version = data.get("version", "1.0")
        
        if version == "1.0":
            data = SchemaMigration.migrate_v1_to_v2(data)
            version = "2.0"
        
        if version == "2.0":
            data = SchemaMigration.migrate_v2_to_v3(data)
            version = "3.0"
        
        return data


class VersionedExtractor:
    """Extractor that handles multiple schema versions"""
    
    SCHEMA_VERSIONS = {
        "1.0": TaskV1,
        "2.0": TaskV2,
        "3.0": TaskV3,
    }
    
    LATEST_VERSION = "3.0"
    
    @classmethod
    def extract_with_version(
        cls,
        data: dict,
        target_version: str = None
    ) -> BaseModel:
        """
        Extract with specific schema version
        
        If target_version is None, uses latest version
        """
        if target_version is None:
            target_version = cls.LATEST_VERSION
        
        # Migrate data to target version if needed
        current_version = data.get("version", "1.0")
        if current_version != target_version:
            # Migrate to latest first, then downgrade if needed
            if current_version < target_version:
                data = SchemaMigration.migrate_any_to_latest(data)
        
        # Validate with target schema
        schema = cls.SCHEMA_VERSIONS[target_version]
        return schema(**data)


class ShadowModeComparison:
    """Compare old and new schema versions in shadow mode"""
    
    def __init__(self):
        self.comparisons = []
    
    def compare_versions(
        self,
        data: dict,
        old_version: str,
        new_version: str
    ) -> dict:
        """
        Run extraction with both versions and compare
        
        Returns comparison results
        """
        try:
            old_result = VersionedExtractor.extract_with_version(data, old_version)
            old_success = True
            old_data = old_result.model_dump()
        except Exception as e:
            old_success = False
            old_data = None
            old_error = str(e)
        
        try:
            # Ensure data has the new version
            data_copy = {**data, "version": new_version}
            new_result = VersionedExtractor.extract_with_version(data_copy, new_version)
            new_success = True
            new_data = new_result.model_dump()
        except Exception as e:
            new_success = False
            new_data = None
            new_error = str(e)
        
        # Compare results
        comparison = {
            "input": data,
            "old_version": old_version,
            "new_version": new_version,
            "old_success": old_success,
            "new_success": new_success,
            "old_data": old_data,
            "new_data": new_data,
            "match": old_data == new_data if (old_success and new_success) else False,
        }
        
        if not old_success:
            comparison["old_error"] = old_error
        if not new_success:
            comparison["new_error"] = new_error
        
        self.comparisons.append(comparison)
        return comparison
    
    def summary(self) -> dict:
        """Get summary of shadow mode testing"""
        total = len(self.comparisons)
        if total == 0:
            return {}
        
        both_success = sum(1 for c in self.comparisons if c["old_success"] and c["new_success"])
        only_old = sum(1 for c in self.comparisons if c["old_success"] and not c["new_success"])
        only_new = sum(1 for c in self.comparisons if not c["old_success"] and c["new_success"])
        both_fail = sum(1 for c in self.comparisons if not c["old_success"] and not c["new_success"])
        
        return {
            "total_comparisons": total,
            "both_success": both_success,
            "only_old_success": only_old,
            "only_new_success": only_new,
            "both_fail": both_fail,
            "new_version_success_rate": (both_success + only_new) / total,
        }


def demonstrate_schema_evolution():
    """Demonstrate schema evolution and migration"""
    
    print("=" * 60)
    print("Example 8: Schema Evolution")
    print("=" * 60)
    
    # Test data in different versions
    v1_data = {
        "version": "1.0",
        "title": "Fix authentication bug",
        "priority": 4
    }
    
    v2_data = {
        "version": "2.0",
        "title": "Implement dashboard feature",
        "priority": 3,
        "category": "feature",
        "description": "Create analytics dashboard"
    }
    
    v3_data = {
        "version": "3.0",
        "title": "Update documentation",
        "priority": 2,
        "category": "docs",
        "description": "Update API documentation",
        "tags": ["docs", "api"],
        "estimated_hours": 4.0
    }
    
    # Demonstrate migrations
    print("\n1. Schema Migrations:")
    print("-" * 60)
    
    print("\n   V1 → V2 Migration:")
    print(f"   Input:  {v1_data}")
    migrated_v2 = SchemaMigration.migrate_v1_to_v2(v1_data)
    print(f"   Output: {migrated_v2}")
    
    print("\n   V2 → V3 Migration:")
    print(f"   Input:  {v2_data}")
    migrated_v3 = SchemaMigration.migrate_v2_to_v3(v2_data)
    print(f"   Output: {migrated_v3}")
    
    print("\n   V1 → V3 (Direct):")
    print(f"   Input:  {v1_data}")
    migrated_latest = SchemaMigration.migrate_any_to_latest(v1_data)
    print(f"   Output: {migrated_latest}")
    
    # Demonstrate versioned extraction
    print("\n2. Versioned Extraction:")
    print("-" * 60)
    
    for version in ["1.0", "2.0", "3.0"]:
        print(f"\n   Extracting with schema v{version}:")
        try:
            if version == "1.0":
                result = VersionedExtractor.extract_with_version(v1_data, version)
            elif version == "2.0":
                result = VersionedExtractor.extract_with_version(v2_data, version)
            else:
                result = VersionedExtractor.extract_with_version(v3_data, version)
            
            print(f"   ✅ Success: {result.model_dump_json(indent=6)}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Demonstrate shadow mode testing
    print("\n3. Shadow Mode Testing:")
    print("-" * 60)
    
    shadow = ShadowModeComparison()
    
    test_cases = [
        {"version": "2.0", "title": "Fix bug 1", "priority": 4, "category": "bug"},
        {"version": "2.0", "title": "Add feature 2", "priority": 3, "category": "feature"},
        {"version": "2.0", "title": "Update docs", "priority": 2, "category": "docs"},
    ]
    
    print("\n   Comparing V2 vs V3:")
    for i, test_case in enumerate(test_cases, 1):
        result = shadow.compare_versions(test_case, "2.0", "3.0")
        status = "✅" if result["new_success"] else "❌"
        print(f"   {status} Test {i}: {test_case['title'][:30]}")
        print(f"      Old success: {result['old_success']}, New success: {result['new_success']}")
    
    print("\n   Shadow Mode Summary:")
    summary = shadow.summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.1%}")
        else:
            print(f"   {key}: {value}")
    
    # Backward compatibility check
    print("\n4. Backward Compatibility:")
    print("-" * 60)
    
    print("\n   Can V3 schema handle V2 data?")
    try:
        v2_in_v3 = TaskV3(**v2_data)
        print(f"   ✅ Yes: {v2_in_v3.model_dump_json(indent=6)}")
    except Exception as e:
        print(f"   ❌ No: {e}")
    
    print("\n   Can V2 schema handle V1 data (after migration)?")
    try:
        migrated = SchemaMigration.migrate_v1_to_v2(v1_data)
        v1_in_v2 = TaskV2(**migrated)
        print(f"   ✅ Yes: {v1_in_v2.model_dump_json(indent=6)}")
    except Exception as e:
        print(f"   ❌ No: {e}")
    
    print("\n" + "=" * 60)
    print("Schema evolution demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_schema_evolution()
