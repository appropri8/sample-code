package terraform.iam

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_role_policy"
    policy := json.unmarshal(resource.change.after.policy)
    statement := policy.Statement[_]
    
    # Block wildcard actions
    statement.Action == "*"
    msg := sprintf("IAM policy '%s' uses wildcard action '*'. Use specific actions instead.", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_role_policy"
    policy := json.unmarshal(resource.change.after.policy)
    statement := policy.Statement[_]
    
    # Block wildcard resources
    statement.Resource == "*"
    msg := sprintf("IAM policy '%s' uses wildcard resource '*'. Use specific resource ARNs instead.", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_role_policy"
    policy := json.unmarshal(resource.change.after.policy)
    statement := policy.Statement[_]
    
    # Block overly broad service permissions
    statement.Action == "s3:*"
    msg := sprintf("IAM policy '%s' grants s3:* permissions. Use specific S3 actions (e.g., s3:GetObject, s3:PutObject).", [resource.address])
}

# Allow exception for specific use cases (documented in allow-list)
allow {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_role_policy"
    resource.address in data.exceptions.iam_wildcards
}
