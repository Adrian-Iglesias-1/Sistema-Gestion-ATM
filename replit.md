# Sistema de Gestión ATM

## Overview

This is a Streamlit-based ATM management system designed to process and match work orders with downtime records. The application allows users to upload Excel files containing work order data and downtime logs, then automatically identifies correlations between maintenance activities and ATM outages within configurable time tolerances. The system provides a web interface for data visualization and analysis to help optimize ATM maintenance operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework
- **UI Components**: 
  - Multi-column layout with sidebar configuration
  - File upload widgets for Excel processing
  - Interactive parameter controls for time tolerance settings
  - Session state management for data persistence across interactions

### Backend Architecture
- **Modular Design**: Separation of concerns with dedicated utility modules
  - `DataProcessor`: Handles Excel file parsing, data validation, and cleaning
  - `WorkOrderMatcher`: Implements matching algorithms between work orders and downtime records
- **Data Processing Pipeline**: 
  - File validation and format checking
  - Data cleaning and standardization
  - Time-based correlation analysis with configurable tolerance windows

### Data Storage Solutions
- **Session-based Storage**: Uses Streamlit's session state for temporary data persistence
- **File Processing**: Direct Excel file processing without permanent storage
- **In-memory Operations**: All data processing occurs in memory using pandas DataFrames

### Data Models
- **Work Orders**: Requires ATM_ID, Fecha_Hora (datetime), and Descripcion fields
- **Downtime Records**: Requires ATM_ID, Fecha_Inicio, Fecha_Fin (datetime range), and Causa fields
- **Matching Logic**: Time-based correlation within configurable minute tolerances

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Pandas**: Data manipulation and analysis library for Excel processing
- **NumPy**: Numerical computing support for data operations
- **IO**: Standard library for file handling operations

### File Format Support
- **Excel Processing**: Supports .xlsx and .xls file formats
- **Data Validation**: Built-in column validation and data type checking

### Configuration
- **Time Tolerance**: Configurable matching tolerance (1-180 minutes)
- **Multi-language Support**: Spanish language interface and field names