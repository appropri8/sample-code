/**
 * Conflict resolution handler
 * 
 * Simple merge function that takes two versions of a profile/settings object,
 * applies field-level rules, and writes merged result
 */

interface Profile {
  id: string;
  email: string;
  displayName: string;
  preferences: {
    theme: string;
    language: string;
    notifications: boolean;
  };
  version: number;
  updatedAt: Date;
  region?: string;
}

interface ConflictVersions {
  version1: Profile;
  version2: Profile;
  detectedAt: Date;
}

class ConflictResolver {
  /**
   * Merge two profile versions
   * 
   * Rules:
   * - Email: use most recent (by timestamp)
   * - Display name: use most recent
   * - Preferences: merge field by field, use most recent for each
   */
  mergeProfiles(versions: ConflictVersions): Profile {
    const { version1, version2 } = versions;
    
    // Determine which is more recent
    const v1Newer = version1.updatedAt > version2.updatedAt;
    const newer = v1Newer ? version1 : version2;
    const older = v1Newer ? version2 : version1;

    // Merge email (use most recent)
    const email = newer.email;

    // Merge display name (use most recent)
    const displayName = newer.displayName;

    // Merge preferences (field-level, use most recent for each)
    const preferences = {
      theme: this.mergeField(version1.preferences.theme, version2.preferences.theme, version1.updatedAt, version2.updatedAt),
      language: this.mergeField(version1.preferences.language, version2.preferences.language, version1.updatedAt, version2.updatedAt),
      notifications: this.mergeField(version1.preferences.notifications, version2.preferences.notifications, version1.updatedAt, version2.updatedAt)
    };

    // Use higher version number + 1
    const version = Math.max(version1.version, version2.version) + 1;

    return {
      id: version1.id, // Same ID
      email,
      displayName,
      preferences,
      version,
      updatedAt: new Date(),
      region: newer.region // Use region from newer version
    };
  }

  /**
   * Merge a single field, using the most recent value
   */
  private mergeField<T>(
    value1: T,
    value2: T,
    timestamp1: Date,
    timestamp2: Date
  ): T {
    // If one is undefined/null, use the other
    if (value1 === undefined || value1 === null) {
      return value2;
    }
    if (value2 === undefined || value2 === null) {
      return value1;
    }

    // Use most recent
    return timestamp1 > timestamp2 ? value1 : value2;
  }

  /**
   * Merge counters (additive)
   */
  mergeCounters(
    counter1: { id: string; value: number; version: number },
    counter2: { id: string; value: number; version: number }
  ): { id: string; value: number; version: number } {
    // For counters, we sum the increments
    // In practice, you'd track increments separately
    // This is a simplified version
    
    const baseValue = Math.min(counter1.value, counter2.value);
    const increment1 = counter1.value - baseValue;
    const increment2 = counter2.value - baseValue;
    
    return {
      id: counter1.id,
      value: baseValue + increment1 + increment2,
      version: Math.max(counter1.version, counter2.version) + 1
    };
  }

  /**
   * Merge sets (union)
   */
  mergeSets<T>(
    set1: { id: string; items: T[]; version: number },
    set2: { id: string; items: T[]; version: number }
  ): { id: string; items: T[]; version: number } {
    // Union of both sets
    const combined = [...set1.items, ...set2.items];
    const unique = Array.from(new Set(combined.map(item => JSON.stringify(item))))
      .map(str => JSON.parse(str));

    return {
      id: set1.id,
      items: unique,
      version: Math.max(set1.version, set2.version) + 1
    };
  }
}

class ConflictHandler {
  constructor(
    private resolver: ConflictResolver,
    private store: {
      findOne: (id: string) => Promise<Profile | null>;
      updateOne: (id: string, profile: Profile) => Promise<void>;
      markConflict: (id: string, versions: ConflictVersions) => Promise<void>;
    }
  ) {}

  /**
   * Handle conflict by merging and storing
   */
  async resolveConflict(
    entityId: string,
    versions: ConflictVersions
  ): Promise<Profile> {
    // Merge versions
    const merged = this.resolver.mergeProfiles(versions);

    // Store merged result
    await this.store.updateOne(entityId, merged);

    return merged;
  }

  /**
   * Detect and handle conflict
   */
  async detectAndResolve(
    entityId: string,
    newVersion: Profile
  ): Promise<Profile> {
    const current = await this.store.findOne(entityId);

    if (!current) {
      // No conflict, just create
      await this.store.updateOne(entityId, newVersion);
      return newVersion;
    }

    // Check if versions conflict
    if (current.version === newVersion.version) {
      // Same version - might be a conflict
      const versions: ConflictVersions = {
        version1: current,
        version2: newVersion,
        detectedAt: new Date()
      };

      // Mark conflict for review (optional)
      await this.store.markConflict(entityId, versions);

      // Auto-resolve by merging
      return await this.resolveConflict(entityId, versions);
    }

    // Version mismatch - use optimistic locking
    if (newVersion.version <= current.version) {
      // Stale version, reject
      throw new Error(
        `Version conflict: current version is ${current.version}, provided ${newVersion.version}`
      );
    }

    // Newer version, update
    await this.store.updateOne(entityId, newVersion);
    return newVersion;
  }
}

// Example usage
async function example() {
  const resolver = new ConflictResolver();
  
  const mockStore = {
    entities: new Map<string, Profile>(),
    
    async findOne(id: string): Promise<Profile | null> {
      return this.entities.get(id) || null;
    },
    
    async updateOne(id: string, profile: Profile): Promise<void> {
      this.entities.set(id, profile);
    },
    
    async markConflict(id: string, versions: ConflictVersions): Promise<void> {
      console.log(`Conflict detected for ${id}:`, {
        version1: versions.version1.version,
        version2: versions.version2.version
      });
    }
  };

  const handler = new ConflictHandler(resolver, mockStore);

  // Create initial profile
  const profile1: Profile = {
    id: 'user-123',
    email: 'user@example.com',
    displayName: 'John Doe',
    preferences: {
      theme: 'dark',
      language: 'en',
      notifications: true
    },
    version: 1,
    updatedAt: new Date('2025-11-22T10:00:00Z'),
    region: 'us-east'
  };

  await mockStore.updateOne('user-123', profile1);

  // Simulate concurrent update from different region
  const profile2: Profile = {
    id: 'user-123',
    email: 'user@example.com',
    displayName: 'John D.',
    preferences: {
      theme: 'light', // Changed
      language: 'en',
      notifications: false // Changed
    },
    version: 1, // Same version (conflict!)
    updatedAt: new Date('2025-11-22T10:01:00Z'), // Slightly newer
    region: 'ap-southeast'
  };

  // Detect and resolve conflict
  const resolved = await handler.detectAndResolve('user-123', profile2);
  console.log('Resolved profile:', resolved);
  console.log('Theme (should be light, from newer):', resolved.preferences.theme);
  console.log('Notifications (should be false, from newer):', resolved.preferences.notifications);
}

export {
  ConflictResolver,
  ConflictHandler,
  Profile,
  ConflictVersions
};

