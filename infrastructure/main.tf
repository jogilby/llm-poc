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

  ingress {
    description      = "Allow SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"] # Open to the world, restrict this for security
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
# IAM Role and Instance Profile
###############################################################################
resource "aws_iam_role" "ec2_role" {
  name               = "llm-ec2-role"
  assume_role_policy = jsonencode({
    Version : "2012-10-17"
    Statement : [
      {
        Effect : "Allow"
        Principal : {
          Service : "ec2.amazonaws.com"
        }
        Action : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "ec2_policy" {
  name        = "llm-ec2-policy"
  description = "Policy for EC2 to access ECR and optional CloudWatch Logs"
  policy      = jsonencode({
    Version : "2012-10-17"
    Statement : [
      # ECR Permissions
      {
        Effect : "Allow"
        Action : [
          "ecr:GetAuthorizationToken",     # Required to authenticate Docker with ECR
          "ecr:BatchGetImage",             # Required to pull images
          "ecr:GetDownloadUrlForLayer"    # Required to pull layers
        ]
        Resource : "*"
      },
      # CloudWatch Logs (Optional)
      {
        Effect   : "Allow"
        Action   : "logs:*"
        Resource : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_policy_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ec2_policy.arn
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "llm-ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
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
  iam_instance_profile        = aws_iam_instance_profile.ec2_instance_profile.name

  # Configure as a Spot Instance
  instance_market_options {
    market_type = "spot"

    spot_options {
      spot_instance_type = "one-time" # Ensures it's a one-time request
    }
  }

  # Increase the size of the root block device
  root_block_device {
    volume_size = 48           # Size in GB
    volume_type = "gp2"        # General-purpose SSD (you can use gp3, io1, etc.)
    delete_on_termination = true # Automatically delete the volume when the instance is terminated
  }

user_data = <<-EOF
#!/bin/bash
# Upgrade to latest Amazon Linux 2023 release
dnf upgrade --releasever=2023.6.20250123 -y

# Detect the unallocated disk (assume it's /dev/nvme1n1 for this example)
DEVICE="/dev/nvme1n1"
MOUNT_POINT="/mnt/data"

# Check if the device exists
if [ -b $DEVICE ]; then
  # Check if the device is already formatted
  if ! blkid $DEVICE; then
    # If not formatted, format it with ext4
    mkfs.ext4 $DEVICE
  fi

  # Create a mount point and mount the device
  mkdir -p $MOUNT_POINT
  mount $DEVICE $MOUNT_POINT

  # Ensure the device is mounted on reboot
  echo "$DEVICE $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab
  sudo chmod 777 /mnt/data
else
  echo "Device $DEVICE not found. Skipping disk setup."
fi

# Add NVIDIA package repository
rpm --import https://developer.download.nvidia.com/compute/cuda/repos/fedora36/x86_64/7fa2af80.pub
curl -O https://developer.download.nvidia.com/compute/cuda/repos/fedora36/x86_64/cuda-repo-fedora36-12-2-local-12.2.128-1.x86_64.rpm
rpm -i cuda-repo-fedora36-12-2-local-12.2.128-1.x86_64.rpm

# Enable the NVIDIA repository and install the CUDA Toolkit
dnf clean all
dnf module disable -y nvidia-driver
dnf install -y cuda

# Verify installation
nvidia-smi
nvcc --version

# Add CUDA to the PATH and LD_LIBRARY_PATH
echo "export PATH=/usr/local/cuda/bin:\$PATH" >> /etc/profile.d/cuda.sh
echo "export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH" >> /etc/profile.d/cuda.sh
source /etc/profile.d/cuda.sh

# Confirm CUDA is properly installed
nvidia-smi > /tmp/nvidia-smi-output.txt
nvcc --version > /tmp/nvcc-version-output.txt

# Install Docker
dnf install -y docker
systemctl enable docker
systemctl start docker

# Set up docker group and add ec2-user
groupadd docker || true
usermod -a -G docker ec2-user

# Restart Docker to ensure all changes take effect
systemctl restart docker

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 230557269713.dkr.ecr.us-east-1.amazonaws.com

# Pull the Docker image
docker pull 230557269713.dkr.ecr.us-east-1.amazonaws.com/poc/llm-poc:latest

# Run the Docker container
docker run -d -p 80:80 230557269713.dkr.ecr.us-east-1.amazonaws.com/poc/llm-poc:latest

EOF
}

###############################################################################
# Outputs
###############################################################################
output "spot_instance_public_ip" {
  description = "The public IP of the Spot Instance"
  value       = aws_instance.llm_spot_instance.public_ip
}