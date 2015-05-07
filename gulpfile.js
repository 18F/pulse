var gulp        = require('gulp'),
    sass        = require('gulp-sass'),
    watch       = require('gulp-watch'),
    rename      = require('gulp-rename'),
    livereload  = require('gulp-livereload');

gulp.task('sass', function() {
    return gulp.src('assets/scss/main.scss')
        .pipe(sass())
        .pipe(gulp.dest('assets/css'))
        .pipe(livereload());
});

gulp.task('watch', function() {
    livereload.listen();
    gulp.watch('assets/scss/**/*', ['sass']);
    gulp.watch('index.html')
    	.on('change', livereload.changed);
});

gulp.task('default', ['sass', 'watch']);

gulp.task('travis', function() {
    return gulp.src('assets/scss/main.scss')
    .pipe(sass())
    .pipe(gulp.dest('assets/css'));
});
