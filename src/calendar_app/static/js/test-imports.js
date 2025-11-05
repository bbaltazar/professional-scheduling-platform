// Incremental module loading test
console.log('🔍 Starting incremental module test...');

try {
    console.log('1. Importing utils...');
    const utils = await import('./utils.js');
    console.log('✅ utils loaded:', utils);

    console.log('2. Importing clients...');
    const clients = await import('./clients.js');
    console.log('✅ clients loaded:', clients);
    console.log('   clientState:', clients.clientState);

    console.log('3. Importing navigation...');
    const navigation = await import('./navigation.js');
    console.log('✅ navigation loaded');

    console.log('4. Importing bookings...');
    const bookings = await import('./bookings.js');
    console.log('✅ bookings loaded');

    console.log('5. Importing schedule...');
    const schedule = await import('./schedule.js');
    console.log('✅ schedule loaded');

    console.log('6. Importing services...');
    const services = await import('./services.js');
    console.log('✅ services loaded');

    console.log('7. Importing workplaces...');
    const workplaces = await import('./workplaces.js');
    console.log('✅ workplaces loaded');

    console.log('8. Importing client-detail...');
    const clientDetail = await import('./client-detail.js');
    console.log('✅ client-detail loaded');

    console.log('🎉 ALL MODULES LOADED SUCCESSFULLY!');
    console.log('Exposing clientState to window...');
    window.clientState = clients.clientState;
    console.log('window.clientState:', window.clientState);

} catch (error) {
    console.error('❌ MODULE LOADING FAILED:', error);
    console.error('Error details:', error.message);
    console.error('Stack trace:', error.stack);
}
