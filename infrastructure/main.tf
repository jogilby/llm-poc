###############################################################################
# Provider Configuration
###############################################################################
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

###############################################################################
# VPC and Security Group
###############################################################################
data "aws_vpc" "specified" {
  id = "vpc-0fd9390ae6c5f4ced" # Use the specific VPC ID
}

data "aws_subnets" "specified_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.specified.id]
  }
}

resource "aws_security_group" "llm_sg" {
  name        = "llm-poc-sg"
  description = "Security group for LLM POC"
  vpc_id      = data.aws_vpc.specified.id

  ingress {
    description      = "Allow HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Allow HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

###############################################################################
# Spot Instance Request
###############################################################################
resource "aws_instance" "llm_spot_instance" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.specified_subnets.ids[0]
  vpc_security_group_ids      = [aws_security_group.llm_sg.id]
  associate_public_ip_address = true
  key_name                    = var.key_name

  # Configure as a Spot Instance
  instance_market_options {
    market_type = "spot"

    spot_options {
      spot_instance_type = "one-time" # Ensures it's a one-time request
      max_price          = var.spot_max_price # Optional: specify your max bid
    }
  }

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    amazon-linux-extras install docker -y
    service docker start
    usermod -a -G docker ec2-user
  EOF
}

###############################################################################
# Outputs
###############################################################################
output "spot_instance_public_ip" {
  description = "The public IP of the Spot Instance"
  value       = aws_instance.llm_spot_instance.public_ip
}