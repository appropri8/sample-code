package terraform.require_tags

test_resource_missing_all_tags {
  input := {
    "resource_changes": [
      {
        "address": "azurerm_storage_account.payments",
        "type": "azurerm_storage_account",
        "change": {
          "after": {}
        }
      }
    ]
  }
  count(deny) > 0
}

test_resource_missing_some_tags {
  input := {
    "resource_changes": [
      {
        "address": "azurerm_key_vault.payments",
        "type": "azurerm_key_vault",
        "change": {
          "after": {
            "tags": {
              "Owner": "payments-team"
            }
          }
        }
      }
    ]
  }
  count(deny) > 0
}

test_resource_has_all_tags {
  input := {
    "resource_changes": [
      {
        "address": "azurerm_postgresql_flexible_server.payments",
        "type": "azurerm_postgresql_flexible_server",
        "change": {
          "after": {
            "tags": {
              "Owner": "payments-team",
              "Env": "production",
              "BackupPolicy": "7d"
            }
          }
        }
      }
    ]
  }
  count(deny) == 0
}
