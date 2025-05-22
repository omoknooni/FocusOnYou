resource "aws_cloudfront_origin_access_control" "media_bucket" {
    name = "focusonyou-media-bucket"
    description = "OAC for Focus On You Media Bucket"
    origin_access_control_origin_type = "s3"
    signing_behavior = "always"
    signing_protocol = "sigv4"
}

resource "aws_cloudfront_distribution" "media_bucket_cdn" {
    enabled = true
    comment = "Focus On You Media Bucket CDN"

    origin {
      origin_id = "S3-${aws_s3_bucket.media_bucket.id}"
      domain_name = aws_s3_bucket.media_bucket.bucket_regional_domain_name
      origin_access_control_id = aws_cloudfront_origin_access_control.media_bucket.id
    }

    default_cache_behavior {
      target_origin_id = "S3-${aws_s3_bucket.media_bucket.id}"
      viewer_protocol_policy = "redirect-to-https"
      allowed_methods = ["GET", "HEAD"]
      cached_methods = ["GET", "HEAD"]
      cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"  // Managed-CachingOptimized
    }

    restrictions {
        geo_restriction {
            restriction_type = "none"
            locations = []
        }
    }
    viewer_certificate {
      cloudfront_default_certificate = true
    }
}