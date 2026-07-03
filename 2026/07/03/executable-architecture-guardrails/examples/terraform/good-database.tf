# examples/terraform/good-database.tf
# Compliant database configuration with encryption, backup, and tags.

resource "azurerm_postgresql_flexible_server" "payments" {
  name                   = "payments-db-prod"
  resource_group_name    = azurerm_resource_group.payments.name
  location               = "eastus"
  version                = "14"
  delegated_subnet_id    = azurerm_subnet.payments.id
  private_dns_zone_id    = azurerm_private_dns_zone.payments.id

  administrator_login    = "payments_admin"
  administrator_password = random_password.db_password.result
  storage_mb             = 32768
  sku_name               = "GP_Standard_D4s_v3"
  backup_retention_days  = 7
  geo_redundant_backup_enabled = true

  tags = {
    Owner           = "payments-team"
    Env             = "production"
    BackupPolicy    = "7d"
    DataClassification = "confidential"
  }
}

resource "azurerm_postgresql_flexible_server_configuration" "pg" {
  name      = "pg_stat_statements.track_utility"
  server_id = azurerm_postgresql_flexible_server.payments.id
  value     = "on"
}
