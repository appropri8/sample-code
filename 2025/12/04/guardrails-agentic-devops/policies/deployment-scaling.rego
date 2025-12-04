# Open Policy Agent (OPA) policy for deployment scaling
# This policy enforces rules around when deployments can be scaled

package deployment.scaling

import future.keywords.if

# Default deny
default allow = false

# Allow scaling if all conditions met
allow if {
    input.tool == "scale_deployment"
    input.context.environment != "production"  # Allow in non-prod
}

allow if {
    input.tool == "scale_deployment"
    input.context.environment == "production"
    is_business_hours(input.context.time)
    within_scale_limits(input)
    not in_cooldown(input)
}

# Check if within business hours (9 AM - 5 PM UTC)
is_business_hours(time) if {
    hour := time[11:13]  # Extract hour from ISO timestamp
    hour >= "09"
    hour < "17"
}

# Check if scale factor is within limits
within_scale_limits(input) if {
    current := input.context.current_replicas
    target := input.parameters.replicas
    
    # Max 2x scale-up in production
    scale_factor := target / current
    scale_factor <= 2.0
}

# Check if deployment is in cooldown (scaled in last 10 minutes)
in_cooldown(input) if {
    # This would check against a history store
    # Simplified for example - in production, query a database
    false
}

# Escalate for large changes
escalate if {
    input.tool == "scale_deployment"
    input.context.environment == "production"
    not is_business_hours(input.context.time)
}

escalate if {
    input.tool == "scale_deployment"
    current := input.context.current_replicas
    target := input.parameters.replicas
    scale_factor := target / current
    scale_factor > 2.0
}
