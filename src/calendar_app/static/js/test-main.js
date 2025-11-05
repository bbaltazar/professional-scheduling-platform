// TEST FILE - Does this execute?
console.log('🔥🔥🔥 TEST FILE IS EXECUTING! 🔥🔥🔥');

console.log('Attempting to import clients...');
import * as clients from './clients.js';
console.log('✅ clients imported');
console.log('clients module keys:', Object.keys(clients));
console.log('clients.clientState:', clients.clientState);
console.log('typeof clients.clientState:', typeof clients.clientState);

// Try to access it directly
import { clientState } from './clients.js';
console.log('Direct import clientState:', clientState);
console.log('Direct import typeof:', typeof clientState);
