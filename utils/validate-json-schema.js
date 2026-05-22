#!/usr/bin/env node

/**
 * JSON Schema validator for Practice Language JSON
 * Usage: node validate-json-schema.js <path-to-json-file>
 */

const fs = require('fs');
const path = require('path');
const Ajv = require('ajv/dist/2020');
const addFormats = require('ajv-formats');

// Get file path from arguments
const jsonFile = process.argv[2];
if (!jsonFile) {
  console.error('Usage: node validate-json-schema.js <path-to-json-file>');
  process.exit(1);
}

// Load schema
const schemaPath = path.join(__dirname, '../deps/language.schema.json');
const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

// Load JSON to validate
const data = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));

// Create AJV instance for 2020-12 with strict mode disabled for compatibility
const ajv = new Ajv({
  allErrors: true,
  verbose: true,
  strict: false
});
addFormats(ajv);

// Compile schema
let validate;
try {
  validate = ajv.compile(schema);
} catch (err) {
  console.error('Schema compilation error:', err.message);
  process.exit(1);
}

// Validate
const valid = validate(data);

if (valid) {
  console.log('✓ JSON is valid against schema');
  process.exit(0);
} else {
  console.log('✗ JSON validation failed\n');
  console.log('ERRORS FOUND:');
  console.log('=============\n');

  validate.errors.forEach((err, idx) => {
    console.log(`${idx + 1}. ${err.instancePath || '(root)'}`);
    console.log(`   Issue: ${err.message}`);
    if (err.params) {
      console.log(`   Details: ${JSON.stringify(err.params)}`);
    }
    if (err.schemaPath) {
      console.log(`   Schema: ${err.schemaPath}`);
    }
    console.log();
  });

  console.log(`Total errors: ${validate.errors.length}`);
  process.exit(1);
}
