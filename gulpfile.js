var gulp        = require('gulp'),
    sass        = require('gulp-sass'),
    watch       = require('gulp-watch'),
    minifycss   = require('gulp-minify-css'),
    rename      = require('gulp-rename'),
    livereload  = require('gulp-livereload');

gulp.task('sass', function() {
    return gulp.src('scss/main.scss')
        .pipe(sass())
        .pipe(minifycss())
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('css'))
        .pipe(livereload());
});

gulp.task('watch', function() {
    livereload.listen();
    gulp.watch('scss/**/*', ['sass']);
    gulp.watch('index.html')
    	.on('change', livereload.changed);
});

gulp.task('default', ['sass', 'watch']);

gulp.task('travis', function() {
    return gulp.src('scss/main.scss')
    .pipe(sass())
    .pipe(minifycss())
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest('css'));
});
