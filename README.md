# FarmBuddy

## A Multimodal, Multilingual NLP-Driven Intelligent Assistant

## Project Overview

FarmBuddy is a multimodal and multilingual intelligent assistant designed to support farmers with crop advisory, market intelligence, and government scheme navigation.

The system accepts input through:

* Text
* Voice
* Image
* Video

It processes the input using Natural Language Processing (NLP) and multimodal analysis to generate simplified and reliable agricultural guidance.

## Objectives

* Provide accurate crop advisory information
* Detect crop diseases using images and video
* Deliver real-time market price insights
* Explain government schemes in simple language
* Support multilingual farmer interaction
* Prioritize urgent agricultural queries

## System Inputs

### 1. Text Input

Farmers can type queries in any supported language.

### 2. Voice Input

Speech-to-text conversion is used to process spoken queries.

### 3. Image Input

Crop images are analyzed for disease detection.

### 4. Video Input

Short crop videos are processed by:

* Extracting key frames
* Applying image-based disease detection
* Aggregating predictions for final output

## Methodology

### 1. Language Detection and Translation

* Detects input language
* Translates to processing language if required

### 2. Text Preprocessing

* Tokenization
* Lemmatization
* Stop-word removal
* Text normalization

### 3. Intent Classification

* Rule-based intent identification
* Query categorization (market, scheme, crop, disease)

### 4. Named Entity Recognition (NER)

Extracts:

* Crop name
* Disease name
* Location
* Season or contextual keywords

### 5. Image Processing

* Lightweight deep learning model
* Disease classification

### 6. Video Processing

* Frame extraction
* Image-based disease detection
* Result aggregation

### 7. Multimodal Fusion

Combines:

* Text
* Voice
* Image
* Video

To generate accurate responses.

### 8. Response Generation

* Knowledge base matching
* FAQ retrieval
* Simplified output generation
* Multilingual output support

## Technology Stack

* **Programming Language:** Python
* **NLP Techniques:** Tokenization, Lemmatization, NER, Intent Classification
* **Speech Processing:** Speech-to-Text, Text-to-Speech
* **Image & Video Processing:** Lightweight Deep Learning Model
* **Data Storage:** JSON, CSV
* **Interface:** Web Application / Application Interface

## System Workflow

1. User provides input (text/voice/image/video)
2. Input is preprocessed
3. Intent and entities are extracted
4. Disease detection (if image/video)
5. Data retrieved from knowledge base
6. Response generated and simplified
7. Output delivered in user’s language

## Key Features

* Multimodal input support
* Multilingual interaction
* Market intelligence system
* Government scheme navigation
* Crop disease detection
* Priority handling for urgent cases

## Project Status

Under Development

## Conclusion

FarmBuddy demonstrates how NLP and multimodal technologies can improve agricultural advisory systems. By integrating language processing, image analysis, and video interpretation, the system empowers farmers with accessible and reliable information.
