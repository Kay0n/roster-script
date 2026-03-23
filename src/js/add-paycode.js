
// addPayCode(105645, "2026-02-23", {id: 226, name: "LVE-Annual"}, 7.5)
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

    const UNPAID_PAYCODE = { id: 269, name: "LVE-Unpaid" };

    return new Promise((resolve, reject) => {

        const rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
        if (!rosterGrid) return reject("Grid component not found.");

        const gridElement = rosterGrid.getEl().dom;
        const injector = angular.element(gridElement).injector();
        const copyPasteService = injector.get('CopyPasteQuickActionService');
        
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
                startDateTime: `${dateString} 05:00:00.000`, // time based of incercepted payload
                id: null, 
                commentNotes:[], exactScheduledAmountInMinutes: -1, isInherited: false,
                isOnlyCommentChanged: false, isOverrideAccrualActive: false,
                isStartTimeChanged: false, orgJob: {}, overrideAccrualAmountInDays: 0,
                scheduledAmountInMinutes: 0, transferLaborEntries:[], unavailabilityAmountInMinutes: 0
            },
            date: `${dateString} 00:00:00.000`,
            employee: employeeRecord.getData().Dto,
            bypassAccrualWarning: false, 
        };

        const functionName = 'pastePayCodeEditActionChange';

        const updateExtJsGridVisually = (payCodeName) => {
            const eventStore = rosterGrid.getEventStore ? rosterGrid.getEventStore() : rosterGrid.getStore();
            
            const [year, month, day] = dateString.split('-');
            const startDate = new Date(year, month - 1, day, 5, 0); 
            const endDate = new Date(startDate.getTime() + (hours * 60 * 60 * 1000));

            const payCodeVisualData = {
                ResourceId: parseInt(employeeId, 10),
                Name: payCodeName,
                Amount: hours.toString(),
                DefinitionId: "paycodeedit", 
                Draggable: true,
                Resizable: false,
                StartDate: startDate,
                EndDate: endDate,
                label: payCodeName,
                commentsLabel: "Comments",
                Cls: "",
                Dto: functionArgument.scheduledItem 
            };

            const newRecord = Ext.create('krn.Sch.models.EntityItem', payCodeVisualData);
            eventStore.add(newRecord); 
        };


        copyPasteService[functionName](functionArgument)
            .then(response => {
                updateExtJsGridVisually(payCodeObject.name);
                resolve(response);
            })
            .catch(error => {
                const is_overdrawn = (error && (error.errorCode === 1401 || error.errorCode === 9));
                
                if (is_overdrawn) {
                    console.log(`Overdrawn paycode detected, retrying with UNPAID_PAYCODE...`);
                    
                    // use unpaid paycode
                    functionArgument.scheduledItem.payCode = {
                        id: { id: UNPAID_PAYCODE.id },
                        name: UNPAID_PAYCODE.name,
                        type: 1, 
                        unit: -1 
                    };

                    copyPasteService[functionName](functionArgument)
                        .then(response => {
                            updateExtJsGridVisually(UNPAID_PAYCODE.name);
                            resolve(response);
                        })
                        .catch(retryError => reject(retryError));
                } else {
                    reject(error);
                }
            });
    });
};






