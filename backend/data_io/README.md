
# Data I/O Directory

This directory manages all input and output files for the Powerhouse B2B Platform.

## Directory Structure

- **uploads/**: User-uploaded input files
- **outputs/**: Generated outputs and results
- **templates/**: Pre-configured task templates
- **samples/**: Example input files for testing

## Available Templates

### 1. Simple Task Template (`simple_task.json`)
Basic single-agent task execution. Use for straightforward tasks that require one agent.

### 2. Multi-Agent Workflow Template (`multi_agent_workflow.json`)
Coordinate multiple agents with dependencies. Ideal for complex tasks requiring specialized agents.

### 3. Batch Processing Template (`batch_processing.json`)
Process multiple similar inputs efficiently. Perfect for bulk operations.

### 4. Research Pipeline Template (`research_pipeline.json`)
Comprehensive research workflow with multiple stages. Best for in-depth analysis tasks.

## Sample Files

### sample_input_1.json
Business analysis scenario with structured data

### sample_input_2.json
Market research task with specific requirements

### sample_batch.csv
CSV format for batch processing tasks

## Usage

1. **Upload Files**: Use the Data Manager UI to upload your input files
2. **Use Templates**: Select a template that matches your use case
3. **View Samples**: Check sample files to understand the expected format
4. **Download Outputs**: Access generated outputs from the outputs directory

## File Formats Supported

- JSON (recommended for structured tasks)
- CSV (for batch processing)
- TXT (for simple text inputs)
- Any custom format (will be treated as binary)

## Best Practices

1. Name files descriptively
2. Include timestamps in filenames for versioning
3. Use templates as starting points
4. Keep input files organized by project/category
5. Regularly clean up old outputs
