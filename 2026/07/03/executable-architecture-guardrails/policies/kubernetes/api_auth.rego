package architecture.api

deny[msg] {
  input.kind == "Service"
  input.spec.type == "LoadBalancer"
  not input.metadata.annotations["auth REQUIRED"] == "true"
  msg := sprintf("Service '%s' is public but missing auth requirement. Add annotation 'auth REQUIRED=true'.", [input.metadata.name])
}
