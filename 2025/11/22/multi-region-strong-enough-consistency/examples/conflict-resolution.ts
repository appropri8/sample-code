import { ConflictResolver, ConflictHandler, Profile } from '../src/conflict-resolution';

/**
 * Example: Conflict resolution handler
 * 
 * Demonstrates how to merge conflicting versions of data
 */

async function main() {
  const resolver = new ConflictResolver();

  // Mock store
  const mockStore = {
    entities: new Map<string, Profile>(),

    async findOne(id: string): Promise<Profile | null> {
      return this.entities.get(id) || null;
    },

    async updateOne(id: string, profile: Profile): Promise<void> {
      this.entities.set(id, profile);
    },

    async markConflict(id: string, versions: any): Promise<void> {
      console.log(`\n⚠️  Conflict detected for ${id}:`);
      console.log('  Version 1:', {
        version: versions.version1.version,
        updatedAt: versions.version1.updatedAt,
        region: versions.version1.region,
        preferences: versions.version1.preferences
      });
      console.log('  Version 2:', {
        version: versions.version2.version,
        updatedAt: versions.version2.updatedAt,
        region: versions.version2.region,
        preferences: versions.version2.preferences
      });
    }
  };

  const handler = new ConflictHandler(resolver, mockStore);

  // Create initial profile in US East
  console.log('=== Creating Profile in US East ===');
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
  console.log('Created:', profile1);

  // Simulate concurrent update from Asia Pacific (same version = conflict)
  console.log('\n=== Concurrent Update from Asia Pacific ===');
  const profile2: Profile = {
    id: 'user-123',
    email: 'user@example.com',
    displayName: 'John D.', // Changed
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
  console.log('\n=== Resolving Conflict ===');
  const resolved = await handler.detectAndResolve('user-123', profile2);
  console.log('Resolved profile:', {
    id: resolved.id,
    displayName: resolved.displayName,
    preferences: resolved.preferences,
    version: resolved.version,
    region: resolved.region
  });

  // Verify merge results
  console.log('\n=== Verification ===');
  console.log('Theme (should be "light" from newer version):', resolved.preferences.theme);
  console.log('Notifications (should be false from newer version):', resolved.preferences.notifications);
  console.log('Display name (should be "John D." from newer version):', resolved.displayName);
  console.log('Version incremented:', resolved.version === 2);
}

main().catch(console.error);

