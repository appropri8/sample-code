import {
  OptimisticLockingService,
  EntityStore,
  VersionConflictError
} from '../src/optimistic-locking';

/**
 * Example: Optimistic locking with version numbers
 * 
 * Demonstrates how to prevent lost updates using version numbers
 */

async function main() {
  const store = new EntityStore();
  const service = new OptimisticLockingService(store);

  // Create an account
  console.log('=== Creating Account ===');
  const account = await service.create('account-123', { balance: 1000 });
  console.log('Created:', account);

  // Read the account
  console.log('\n=== Reading Account ===');
  const read = await service.read('account-123');
  console.log('Read:', read);
  console.log('Version:', read?.version);

  // Update with correct version
  console.log('\n=== Updating with Correct Version ===');
  try {
    const updated = await service.update({
      id: 'account-123',
      data: { balance: 1500 },
      version: read!.version
    });
    console.log('Updated successfully:', updated);
  } catch (error) {
    if (error instanceof VersionConflictError) {
      console.error('Version conflict:', error.message);
    } else {
      throw error;
    }
  }

  // Try to update with wrong version (simulates concurrent update)
  console.log('\n=== Attempting Update with Wrong Version ===');
  try {
    await service.update({
      id: 'account-123',
      data: { balance: 2000 },
      version: 1 // Wrong version (current is 2)
    });
    console.log('Update succeeded (unexpected)');
  } catch (error) {
    if (error instanceof VersionConflictError) {
      console.log('Expected version conflict:', error.message);
      console.log('Current version:', error.currentVersion);
      console.log('Provided version:', error.providedVersion);
    } else {
      throw error;
    }
  }

  // Read again to see current state
  console.log('\n=== Reading Account Again ===');
  const final = await service.read('account-123');
  console.log('Final state:', final);
}

main().catch(console.error);

