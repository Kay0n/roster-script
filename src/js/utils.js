
/**
 * @returns {Array<Object>}
 */
getEmployees = function() {
    var rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
    var resourceStore = rosterGrid.getResourceStore();
    var employees = resourceStore.data.items.map(r => r.getData());
    return employees;
}



/**
 * @param {string} name
 * 
 * @returns {number|null} 
 */
getEmployeeIdByName = function(name) {
    var rosterGrid = Ext.getCmp('krnScheduleGrid_schedule_by_employee');
    var resourceStore = rosterGrid.getResourceStore();

    // fieldName, value, startIndex, anyMatch, caseSensitive, exactMatch
    var record = resourceStore.findRecord('1', name, 0, false, true, true);
    return record ? record.get('Id') : null;
}



