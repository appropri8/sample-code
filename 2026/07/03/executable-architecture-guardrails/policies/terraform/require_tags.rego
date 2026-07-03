package terraform.require_tags

# Enforce owner, environment, and backup tags on all resources
deny[msg] {
  resource := input.resource_changes[_]
  not resource.change.after.tags
  msg := sprintf("Resource '%s' is missing tags. Add Owner, Env, and BackupPolicy tags.", [resource.address])
}

deny[msg] {
  resource := input.resource_changes[_]
  tags := resource.change.after.tags
  required := {"Owner", "Env", "BackupPolicy"}
  missing := required - object.keys(tags)
  count(missing) > 0
  msg := sprintf("Resource '%s' is missing tags: %s. Required tags: Owner, Env, BackupPolicy.", [resource.address, concat(", ", missing)])
}

# Allow exceptions documented in exceptions.yaml
allow {
  resource := input.resource_changes[_]
  resource.address in data.exceptions.missing_tags
}
