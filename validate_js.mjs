#!/usr/bin/env node
/**
 * JavaScript Module Validator
 * Tests if all JS modules can be imported without syntax errors
 */

console.log('🔍 Validating JavaScript modules...\n');

async function validateModule(modulePath, moduleName) {
    try {
        console.log(`Testing ${moduleName}...`);
        await import(modulePath);
        console.log(`✅ ${moduleName} - Valid\n`);
        return true;
    } catch (error) {
        console.error(`❌ ${moduleName} - ERROR:`);
        console.error(error.message);
        console.error(error.stack);
        console.error('\n');
        return false;
    }
}

async function main() {
    const basePath = './src/calendar_app/static/js/';
    const modules = [
        { path: `${basePath}utils.js`, name: 'utils.js' },
        { path: `${basePath}clients.js`, name: 'clients.js' },
        { path: `${basePath}navigation.js`, name: 'navigation.js' },
        { path: `${basePath}bookings.js`, name: 'bookings.js' },
        { path: `${basePath}schedule.js`, name: 'schedule.js' },
        { path: `${basePath}services.js`, name: 'services.js' },
        { path: `${basePath}workplaces.js`, name: 'workplaces.js' },
        { path: `${basePath}client-detail.js`, name: 'client-detail.js' },
        { path: `${basePath}main.js`, name: 'main.js' },
    ];

    let allValid = true;
    for (const module of modules) {
        const isValid = await validateModule(module.path, module.name);
        if (!isValid) {
            allValid = false;
        }
    }

    console.log('='.repeat(50));
    if (allValid) {
        console.log('✅ All modules are valid!');
        process.exit(0);
    } else {
        console.log('❌ Some modules have errors!');
        process.exit(1);
    }
}

main();
