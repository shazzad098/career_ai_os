// app/static/js/main.js
// Add any JavaScript functionality here
document.addEventListener('DOMContentLoaded', function() {
    // Example: Add confirmation before completing a task
    const completeButtons = document.querySelectorAll('.btn-success');
    completeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to mark this task as completed?')) {
                e.preventDefault();
            }
        });
    });
});