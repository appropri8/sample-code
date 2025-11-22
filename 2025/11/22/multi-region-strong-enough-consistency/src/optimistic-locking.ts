/**
 * Optimistic locking with version numbers
 * 
 * Entity model with version field and update endpoint
 * that compares versions and returns 409 Conflict if mismatch
 */

interface Entity {
  id: string;
  data: any;
  version: number;
  updatedAt: Date;
}

interface UpdateRequest {
  id: string;
  data: any;
  version: number; // Expected current version
}

class EntityStore {
  private entities: Map<string, Entity> = new Map();

  async findOne(id: string): Promise<Entity | null> {
    return this.entities.get(id) || null;
  }

  async updateOne(
    filter: { id: string; version?: number },
    update: { $set: Partial<Entity> }
  ): Promise<{ matchedCount: number; modifiedCount: number }> {
    const entity = this.entities.get(filter.id);
    
    if (!entity) {
      return { matchedCount: 0, modifiedCount: 0 };
    }

    // Check version if provided
    if (filter.version !== undefined && entity.version !== filter.version) {
      return { matchedCount: 0, modifiedCount: 0 };
    }

    // Update entity
    Object.assign(entity, update.$set, {
      version: entity.version + 1,
      updatedAt: new Date()
    });

    this.entities.set(filter.id, entity);

    return { matchedCount: 1, modifiedCount: 1 };
  }

  async insertOne(entity: Entity): Promise<void> {
    if (this.entities.has(entity.id)) {
      throw new Error(`Entity already exists: ${entity.id}`);
    }
    this.entities.set(entity.id, entity);
  }
}

class VersionConflictError extends Error {
  constructor(
    public entityId: string,
    public currentVersion: number,
    public providedVersion: number
  ) {
    super(
      `Version conflict: entity ${entityId} has version ${currentVersion}, but ${providedVersion} was provided`
    );
    this.name = 'VersionConflictError';
  }
}

class OptimisticLockingService {
  constructor(private store: EntityStore) {}

  /**
   * Read entity with version
   */
  async read(id: string): Promise<Entity | null> {
    return await this.store.findOne(id);
  }

  /**
   * Update entity with version check
   */
  async update(request: UpdateRequest): Promise<Entity> {
    const { id, data, version } = request;

    // Read current entity
    const current = await this.store.findOne(id);
    
    if (!current) {
      throw new Error(`Entity not found: ${id}`);
    }

    // Check version
    if (current.version !== version) {
      throw new VersionConflictError(id, current.version, version);
    }

    // Update with version check
    const result = await this.store.updateOne(
      { id, version },
      { $set: { data } }
    );

    if (result.matchedCount === 0) {
      // Version changed between read and update
      const updated = await this.store.findOne(id);
      throw new VersionConflictError(
        id,
        updated?.version || 0,
        version
      );
    }

    // Return updated entity
    const updated = await this.store.findOne(id);
    if (!updated) {
      throw new Error(`Entity not found after update: ${id}`);
    }

    return updated;
  }

  /**
   * Create new entity
   */
  async create(id: string, data: any): Promise<Entity> {
    const entity: Entity = {
      id,
      data,
      version: 1,
      updatedAt: new Date()
    };

    await this.store.insertOne(entity);
    return entity;
  }
}

// Example usage
async function example() {
  const store = new EntityStore();
  const service = new OptimisticLockingService(store);

  // Create entity
  const created = await service.create('account-123', { balance: 1000 });
  console.log('Created:', created);

  // Read entity
  const read = await service.read('account-123');
  console.log('Read:', read);

  // Update with correct version
  try {
    const updated = await service.update({
      id: 'account-123',
      data: { balance: 1500 },
      version: read!.version
    });
    console.log('Updated:', updated);
  } catch (error) {
    if (error instanceof VersionConflictError) {
      console.error('Version conflict:', error.message);
    } else {
      throw error;
    }
  }

  // Try to update with wrong version (should fail)
  try {
    await service.update({
      id: 'account-123',
      data: { balance: 2000 },
      version: 1 // Wrong version
    });
  } catch (error) {
    if (error instanceof VersionConflictError) {
      console.log('Expected version conflict:', error.message);
    } else {
      throw error;
    }
  }
}

export {
  OptimisticLockingService,
  EntityStore,
  Entity,
  UpdateRequest,
  VersionConflictError
};

