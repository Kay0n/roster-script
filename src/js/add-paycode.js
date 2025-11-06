/**
 * Adds a pay code shift to the grid. Results are not visible, 
 * but can be seen upon save and refresh.
 *
 * @param {number} employeeId 
 * @param {string} dateString - format 'YYYY-MM-DD'
 * @param {Object} payCodeObject 
 *   @param {number} payCodeObject.id
 *   @param {string} payCodeObject.name
 * @param {number} hours
 *
 * @returns {void} 
 */
addPayCode = function(employeeId, dateString, payCodeObject, hours) {

    const UNPAID_PAYCODE = { id: 269, name: "LVE-Unpaid"}

    return new Promise((resolve, reject) => {

        const rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
        if (!rosterGrid) return reject("Grid component not found.");

        const gridElement = rosterGrid.getEl().dom;
        if (!gridElement) return reject("Grid DOM element not found");

        const injector = angular.element(gridElement).injector();
        if (!injector) return reject("Angular injector not found");

        const copyPasteService = injector.get('CopyPasteQuickActionService');
        if (!copyPasteService) return reject("'CopyPasteQuickActionService' not found");

        const resourceStore = rosterGrid.getResourceStore();
        const employeeRecord = resourceStore.findRecord('Id', employeeId, 0, false, true, true);
        if (!employeeRecord) return reject(`Employee with ID ${employeeId} not found`);


        const functionArgument = {
            scheduledItem: {
                amount: hours * 60, 
                payCode: {
                    id: { id: payCodeObject.id },
                    name: payCodeObject.name,
                    type: 1, 
                    unit: -1 
                },
                employee: employeeRecord.getData().Dto,
                startDateTime: `${dateString} 05:00:00.000`, // time based off intercepted payloads
                id: null, 
                commentNotes: [], exactScheduledAmountInMinutes: -1, isInherited: false,
                isOnlyCommentChanged: false, isOverrideAccrualActive: false,
                isStartTimeChanged: false, orgJob: {}, overrideAccrualAmountInDays: 0,
                scheduledAmountInMinutes: 0, transferLaborEntries: [], unavailabilityAmountInMinutes: 0
            },
            date: `${dateString} 00:00:00.000`,
            employee: employeeRecord.getData().Dto,
            bypassAccrualWarning: false, 
            
        };

        const functionName = 'pastePayCodeEditActionChange';
        if (typeof copyPasteService[functionName] !== 'function') {
            return reject(`Function '${functionName}' not found on CopyPasteQuickActionService`);
        }


        copyPasteService[functionName](functionArgument)
            .then(response => {
                resolve(response);
            })
            .catch(error => {
                console.error(`Paste operation for ${employeeId} at ${dateString} with pay code ${payCodeObject.name} failed`, error);

                if (error && error.errorCode === 1401) {
                    console.log(`Overdrawn paycode detected, retrying with UNPAID_PAYCODE for ${employeeId} at ${dateString}`);
                    
                    functionArgument.scheduledItem.payCode = {
                        id: { id: UNPAID_PAYCODE.id },
                        name: UNPAID_PAYCODE.name,
                        type: 1, 
                        unit: -1 
                    },

                    copyPasteService[functionName](functionArgument)
                        .then(response => {
                            resolve(response);
                        })
                        .catch(retryError => {
                            console.error(`Retry failed for ${employeeId} at ${dateString} with UNPAID_PAYCODE`, retryError);
                            reject(retryError);
                        });
                } else {
                    reject(error);
                }
            });
    });
}






