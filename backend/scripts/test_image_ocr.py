#!/usr/bin/env python3
"""Test script for Image OCR functionality

Supports both GPT-4o (default) and Gemini (when Vertex AI is configured).

Usage:
    python scripts/test_image_ocr.py [image_url]
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.image_alt_generator import ImageAltGeneratorService, ImageType


async def test_ocr(image_url: str):
    """Test OCR on a given image URL"""
    print("=" * 60)
    print("Image OCR Test")
    print("=" * 60)
    print(f"\nImage URL: {image_url}\n")

    # Initialize service
    service = ImageAltGeneratorService()
    print(f"Provider: {service.provider.value}")
    print(f"Model: {service.gemini_model_name if service.use_vertex_ai else service.openai_model}")
    print("-" * 60)

    # Test article context
    article_context = {
        "title": "測試文章標題",
        "excerpt": "這是測試文章的摘要內容",
        "position": 0,
        "is_featured": True
    }

    # Generate suggestions
    print("\nGenerating alt text...")
    result = await service.generate_suggestions(
        image_id=0,
        image_url=image_url,
        article_context=article_context,
        use_vision=True
    )

    # Display results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)

    print(f"\n📷 Image Type: {result.image_type.value}")
    print(f"🔧 Generation Method: {result.generation_method.value}")
    print(f"🤖 Model Used: {result.model_used}")
    print(f"📊 Tokens Used: {result.tokens_used}")

    if result.detected_text:
        print(f"\n📝 Detected Text (OCR):")
        print("-" * 40)
        print(result.detected_text)
        print("-" * 40)

    print(f"\n✨ Suggested Alt Text (confidence: {result.suggested_alt_text_confidence:.2f}):")
    print(result.suggested_alt_text)

    print(f"\n📄 Suggested Description (confidence: {result.suggested_description_confidence:.2f}):")
    print(result.suggested_description)

    if result.error_message:
        print(f"\n❌ Error: {result.error_message}")

    print("\n" + "=" * 60)
    return result


# Test images
TEST_IMAGES = {
    "infographic": "https://www.epochtimes.com/gb/24/12/20/i14399234/n14399234-0.jpg",  # Example news infographic
    "photo": "https://i.epochtimes.com/assets/uploads/2024/12/id14399234-GettyImages-2191130945-600x400.jpg",  # Example photo
}


if __name__ == "__main__":
    # Get image URL from command line or use default
    if len(sys.argv) > 1:
        image_url = sys.argv[1]
    else:
        # Use a sample image for testing
        print("No image URL provided. Using sample images...\n")

        for img_type, url in TEST_IMAGES.items():
            print(f"\nTesting {img_type} image...")
            try:
                asyncio.run(test_ocr(url))
            except Exception as e:
                print(f"Error testing {img_type}: {e}")
        sys.exit(0)

    asyncio.run(test_ocr(image_url))
