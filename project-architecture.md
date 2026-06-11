# Study Companion - Architecture & System Design

## Project Overview

Study Companion is an AI-powered academic workspace designed to help students organize study materials and generate exam-oriented learning resources from uploaded documents.

The system allows students to create subject-specific workspaces, upload study materials, generate revision notes, generate long-form exam answers, practice quizzes, and interact with an AI assistant that understands the context of the uploaded documents.

---

# Problem Statement

Students often spend significant time manually converting study materials into revision notes, exam answers, and practice questions.

Existing PDF chatbots primarily focus on question-answering and lack academic workflows specifically designed for exam preparation and subject organization.

Study Companion aims to transform study materials into structured learning resources while maintaining subject-specific context through dedicated workspaces.

---

# Objectives

* Organize study materials by subject.
* Convert documents into exam-oriented learning resources.
* Generate quick revision content.
* Generate detailed long-form answers.
* Generate interactive quizzes.
* Provide workspace-specific AI assistance.
* Improve study efficiency and exam preparation.

---

# Core Features

## Workspace Management

Students can create multiple subject-specific workspaces.

Examples:

* Operating Systems
* DWDM
* Machine Learning
* Computer Networks

Each workspace maintains its own documents, generated content, and chat history.

---

## Document Processing

Supported document types:

* PDF
* DOCX (Optional)

The system extracts text from uploaded documents and stores it for future processing.

---

## Revision Mode

Provides concise study material for quick learning and revision.

Output includes:

* Definitions
* Key Concepts
* Types
* Advantages
* Disadvantages
* Applications
* Important Points

Purpose:

Fast revision before exams.

---

## Exam Mode

Generates structured long-form answers suitable for 7–10 mark university questions.

Output includes:

* Introduction
* Explanation
* Types
* Working
* Advantages
* Disadvantages
* Applications
* Conclusion

Purpose:

Deep conceptual understanding and exam preparation.

---

## Quiz Mode

Generates interactive multiple-choice questions from uploaded study material.

Features:

* MCQs
* Difficulty Levels
* Score Tracking
* Instant Feedback

Purpose:

Self-assessment and active learning.

---

## Workspace AI Chat

Students can ask questions related to documents uploaded within a workspace.

The AI uses only workspace-specific study materials to answer questions.

Purpose:

Context-aware academic assistance.

---

# Unique Feature: Subject-Based Workspaces

Unlike traditional PDF chatbots, Study Companion introduces subject-specific workspaces.

Benefits:

* Better organization of study materials.
* Subject isolation.
* Reduced context confusion.
* Improved AI response quality.
* Dedicated chat history per subject.

Example:

Operating Systems Workspace

* Unit1.pdf
* Unit2.pdf
* Revision Notes
* Exam Answers
* Quiz Questions
* AI Chat

DWDM Workspace

* Unit1.pdf
* Quiz
* Chat
* Notes

The AI understands that each workspace represents a unique academic subject.

---

# Technology Stack

## Frontend

* React
* HTML
* CSS
* JavaScript

## Backend

* Python
* FastAPI

## Database

* PostgreSQL

## AI Integration

* Gemini API

## Document Processing

* PyPDF2
* pdfplumber

---

# High-Level Architecture

User

↓

React Frontend

↓

FastAPI Backend

↓

Services Layer

* Workspace Manager
* Document Processor
* AI Engine
* Chat Service

↓

PostgreSQL Database

↓

Gemini AI

↓

Generated Learning Resources

* Revision Notes
* Exam Answers
* Quiz Questions
* Chat Responses

---

# Database Entities

## User

Stores user account information.

## Workspace

Stores subject-specific workspaces.

## Document

Stores uploaded document metadata.

## ExtractedText

Stores extracted text from uploaded documents.

## GeneratedContent

Stores AI-generated outputs.

Types:

* Revision
* Exam
* Quiz

## ChatHistory

Stores workspace-specific conversations.

---

# Development Roadmap

## Phase 1

Requirement Analysis & System Design

## Phase 2

Backend & Database Development

## Phase 3

AI & Document Processing

## Phase 4

Frontend Development

## Phase 5

System Integration & Refinement

## Phase 6

Testing, Validation & Deployment

---

# Expected Outcome

The final system will provide students with a centralized AI-powered study environment capable of transforming academic documents into structured learning resources, improving revision efficiency, exam preparation, and overall understanding of subject material.
