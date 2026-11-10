// Helpers injected into the Kronos schedule iframe. Called from kronos_driver.py as rosterTool.*

window.rosterTool = (function() {

    function getRosterGrid() {
        const rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
        if (!rosterGrid) throw new Error("Grid component not found");
        return rosterGrid;
    }


    /**
     * Turns whatever a Kronos promise rejected with into a readable string.
     */
    function describeError(error) {
        if (error instanceof Error) return error.message;
        if (typeof error === 'string') return error;
        try {
            return JSON.stringify(error).slice(0, 500);
        } catch (_) {
            return String(error);
        }
    }


    /**
     * @returns {Array<Object>}
     */
    function getEmployees() {
        const resourceStore = getRosterGrid().getResourceStore();
        return resourceStore.data.items.map(r => r.getData());
    }


    /**
     * Adds a shift to the grid. Throws if it can't.
     *
     * @param {number} employeeId
     * @param {string} dateString - format 'YYYY-MM-DD'
     * @param {string} timeRange - format 'nnnn-nnnn'
     */
    function addShift(employeeId, dateString, timeRange) {

        const scheduleView = getRosterGrid().normalGrid.getView();
        if (!scheduleView) throw new Error("normalGrid view not found");

        function parseDateTime(dateStr, timeStr) {
            const year = parseInt(dateStr.substring(0, 4), 10);
            const month = parseInt(dateStr.substring(5, 7), 10) - 1; // JS months are 0-indexed
            const day = parseInt(dateStr.substring(8, 10), 10);
            const hours = parseInt(timeStr.substring(0, 2), 10);
            const minutes = parseInt(timeStr.substring(2, 4), 10);
            return new Date(year, month, day, hours, minutes);
        }

        const times = timeRange.split('-');
        const startDate = parseDateTime(dateString, times[0]);
        const endDate = parseDateTime(dateString, times[1]);

        if (endDate < startDate) { // handle overnight shifts
            endDate.setDate(endDate.getDate() + 1);
        }

        const shiftData = {
            ResourceId: parseInt(employeeId, 10),
            Name: timeRange,
            StartDate: startDate,
            EndDate: endDate,
            Draggable: true,
            Resizable: true,
            Cls: ""
        };

        const newShiftRecord = Ext.create('krn.Sch.models.EntityItem', shiftData);
        if (!newShiftRecord) throw new Error("Failed to create an instance of 'krn.Sch.models.EntityItem'");

        scheduleView.fireEvent('shiftCreatedComplete', newShiftRecord, null);
    }


    // rosterTool.addPayCode(105645, "2026-02-23", {id: 226, name: "LVE-Annual"}, 7.5, {id: 269, name: "LVE-Unpaid"})
    /**
     * Adds a pay code to the grid. Results are not visible,
     * but can be seen upon save and refresh.
     *
     * @param {number} employeeId
     * @param {string} dateString - format 'YYYY-MM-DD'
     * @param {{id: number, name: string}} payCode
     * @param {number} hours
     * @param {{id: number, name: string}} fallbackPayCode - used if Kronos says payCode is overdrawn
     *
     * @returns {Promise<{fellBack: boolean}>}
     */
    function addPayCode(employeeId, dateString, payCode, hours, fallbackPayCode) {

        return new Promise((resolve, reject) => {

            const rosterGrid = getRosterGrid();

            const gridElement = rosterGrid.getEl().dom;
            const injector = angular.element(gridElement).injector();
            const copyPasteService = injector.get('CopyPasteQuickActionService');

            const resourceStore = rosterGrid.getResourceStore();
            const employeeRecord = resourceStore.findRecord('Id', employeeId, 0, false, true, true);
            if (!employeeRecord) return reject(`Employee with ID ${employeeId} not found`);

            const toKronosPayCode = (p) => ({ id: { id: p.id }, name: p.name, type: 1, unit: -1 });

            const pasteRequest = {
                scheduledItem: {
                    amount: hours * 60,
                    payCode: toKronosPayCode(payCode),
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

            const showPayCodeInGrid = (payCodeName) => {
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
                    Dto: pasteRequest.scheduledItem
                };

                const newRecord = Ext.create('krn.Sch.models.EntityItem', payCodeVisualData);
                eventStore.add(newRecord);
            };


            copyPasteService.pastePayCodeEditActionChange(pasteRequest)
                .then(() => {
                    showPayCodeInGrid(payCode.name);
                    resolve({ fellBack: false });
                })
                .catch(error => {
                    const isOverdrawn = (error && (error.errorCode === 1401 || error.errorCode === 9));
                    if (!isOverdrawn) return reject(error);

                    console.log(`Overdrawn paycode detected, retrying with ${fallbackPayCode.name}...`);
                    pasteRequest.scheduledItem.payCode = toKronosPayCode(fallbackPayCode);

                    copyPasteService.pastePayCodeEditActionChange(pasteRequest)
                        .then(() => {
                            showPayCodeInGrid(fallbackPayCode.name);
                            resolve({ fellBack: true });
                        })
                        .catch(retryError => reject(retryError));
                });
        });
    }


    return { getEmployees, addShift, addPayCode, describeError };
})();
