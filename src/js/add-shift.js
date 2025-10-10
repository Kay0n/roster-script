
/**
 * Adds a shift to the grid.
 *
 * @param {number} employeeId 
 * @param {string} dateString - format 'YYYY-MM-DD'
 * @param {string} shiftString - format 'nnnn-nnnn'
 *
 * @returns {void} 
 */
addShift = function(employeeId, dateString, shiftString) {

    const rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
    if (!rosterGrid) {
        return console.error("Grid component not found");
    }
    const scheduleView = rosterGrid.normalGrid.getView();
    if (!scheduleView) {
        return console.error("normalGrid view not found");
    }

    function parseDateTime(dateStr, timeStr) {
        const year = parseInt(dateStr.substring(0, 4), 10);
        const month = parseInt(dateStr.substring(5, 7), 10) - 1; // JS months are 0-indexed
        const day = parseInt(dateStr.substring(8, 10), 10);
        const hours = parseInt(timeStr.substring(0, 2), 10);
        const minutes = parseInt(timeStr.substring(2, 4), 10);
        return new Date(year, month, day, hours, minutes);
    }

    const times = shiftString.split('-');
    const startDate = parseDateTime(dateString, times[0]);
    const endDate = parseDateTime(dateString, times[1]);

    if (endDate < startDate) { // handle overnight shifts
        endDate.setDate(endDate.getDate() + 1);
    }

    const shiftData = {
        ResourceId: parseInt(employeeId, 10), 
        Name: shiftString,                     
        StartDate: startDate,
        EndDate: endDate,
        Draggable: true,
        Resizable: true,
        Cls: ""
    };

    const newShiftRecord = Ext.create('krn.Sch.models.EntityItem', shiftData);
    if (!newShiftRecord) {
        return console.error("Failed to create an instance of 'krn.Sch.models.EntityItem'.");
    }

    scheduleView.fireEvent('shiftCreatedComplete', newShiftRecord, null);
    
}
