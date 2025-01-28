variable "aws_region" {
  type        = string
  description = "AWS Region to deploy to"
  default     = "us-east-1"
}

variable "aws_profile" {
  type        = string
  description = "AWS CLI profile to use"
  default     = "default"
}

variable "ami_id" {
  type        = string
  description = "AMI ID for your EC2 instance"
  # Example Amazon Linux 2 AMI in us-east-1
  default     = "ami-0df8c184d5f6ae949"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "g4dn.xlarge"
}

variable "key_name" {
  type        = string
  description = "The name of an existing EC2 KeyPair to enable SSH access"
  default     = "Jan25 Root Key Pair"
}