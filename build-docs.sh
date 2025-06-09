#!/bin/bash

# FastMarkDocs Documentation Build Script
# This script builds and serves the documentation locally using Jekyll

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_SRC_DIR="src/docs"
DOCS_OUTPUT_DIR="docs"
BUILD_DIR="_site"
PORT=4001
HOST="0.0.0.0"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Ruby and Bundler installation
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command_exists ruby; then
        print_error "Ruby is not installed. Please install Ruby first."
        echo "On macOS: brew install ruby"
        echo "On Ubuntu: sudo apt-get install ruby-full"
        exit 1
    fi
    
    if ! command_exists bundle; then
        print_warning "Bundler is not installed. Installing..."
        gem install bundler
    fi
    
    print_success "Dependencies check completed"
}

# Function to install Jekyll dependencies
install_dependencies() {
    print_status "Installing Jekyll dependencies..."
    
    cd "$DOCS_SRC_DIR"
    
    # Configure bundler to install gems locally to avoid permission issues
    if [ ! -f ".bundle/config" ]; then
        print_status "Configuring bundler for local gem installation..."
        bundle config set --local path 'vendor/bundle'
    fi
    
    if [ ! -f "Gemfile.lock" ]; then
        print_status "Installing gems for the first time..."
        bundle install --path vendor/bundle
    else
        print_status "Updating gems..."
        bundle update
    fi
    
    cd - > /dev/null
    print_success "Dependencies installed"
}

# Function to build the documentation
build_docs() {
    print_status "Building documentation..."
    print_status "Source: $DOCS_SRC_DIR/ -> Output: $DOCS_OUTPUT_DIR/"
    
    cd "$DOCS_SRC_DIR"
    
    # Clean previous build
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        print_status "Cleaned previous build"
    fi
    
    # Clean output directory
    if [ -d "../../$DOCS_OUTPUT_DIR" ]; then
        rm -rf "../../$DOCS_OUTPUT_DIR"
        print_status "Cleaned output directory"
    fi
    
    # Build the site
    bundle exec jekyll build --destination "../../$DOCS_OUTPUT_DIR" --verbose
    
    cd - > /dev/null
    print_success "Documentation built successfully"
}

# Function to serve the documentation locally
serve_docs() {
    print_status "Starting local server..."
    print_status "Source: $DOCS_SRC_DIR/ -> Output: $DOCS_OUTPUT_DIR/"
    print_status "Documentation will be available at: http://$HOST:$PORT"
    print_status "Press Ctrl+C to stop the server"
    
    cd "$DOCS_SRC_DIR"
    
    # Serve with live reload
    bundle exec jekyll serve \
        --destination "../../$DOCS_OUTPUT_DIR" \
        --host "$HOST" \
        --port "$PORT" \
        --livereload \
        --incremental \
        --verbose
}

# Function to validate the build
validate_build() {
    print_status "Validating build..."
    
    if [ ! -d "$DOCS_OUTPUT_DIR" ]; then
        print_error "Output directory not found: $DOCS_OUTPUT_DIR"
        exit 1
    fi
    
    if [ ! -f "$DOCS_OUTPUT_DIR/index.html" ]; then
        print_error "Index file not generated"
        exit 1
    fi
    
    # Check for common files
    local files=("getting-started.html" "user-guide.md" "api-reference.html")
    for file in "${files[@]}"; do
        if [ ! -f "$DOCS_OUTPUT_DIR/$file" ]; then
            print_warning "Expected file not found: $file"
        fi
    done
    
    print_success "Build validation completed"
}

# Function to clean build artifacts
clean_build() {
    print_status "Cleaning build artifacts..."
    
    # Clean output directory
    if [ -d "$DOCS_OUTPUT_DIR" ]; then
        rm -rf "$DOCS_OUTPUT_DIR"
        print_status "Removed output directory: $DOCS_OUTPUT_DIR"
    fi
    
    # Clean Jekyll cache and build files in source directory
    if [ -d "$DOCS_SRC_DIR/$BUILD_DIR" ]; then
        rm -rf "$DOCS_SRC_DIR/$BUILD_DIR"
        print_status "Removed source build directory"
    fi
    
    if [ -d "$DOCS_SRC_DIR/.jekyll-cache" ]; then
        rm -rf "$DOCS_SRC_DIR/.jekyll-cache"
        print_status "Removed Jekyll cache"
    fi
    
    if [ -f "$DOCS_SRC_DIR/.jekyll-metadata" ]; then
        rm -f "$DOCS_SRC_DIR/.jekyll-metadata"
        print_status "Removed Jekyll metadata"
    fi
    
    if [ -d "$DOCS_SRC_DIR/.sass-cache" ]; then
        rm -rf "$DOCS_SRC_DIR/.sass-cache"
        print_status "Removed Sass cache"
    fi
    
    print_success "Clean completed"
}

# Function to show help
show_help() {
    echo "FastMarkDocs Documentation Build Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Install dependencies and setup environment"
    echo "  build     Build the documentation"
    echo "  serve     Build and serve documentation locally"
    echo "  validate  Validate the built documentation"
    echo "  clean     Clean build artifacts"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # First time setup"
    echo "  $0 serve     # Build and serve locally"
    echo "  $0 build     # Build only"
    echo ""
    echo "Environment Variables:"
    echo "  DOCS_PORT   Port for local server (default: 4001)"
    echo "  DOCS_HOST   Host for local server (default: 0.0.0.0)"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up documentation environment..."
    
    check_dependencies
    install_dependencies
    
    print_success "Environment setup completed"
    print_status "You can now run: $0 serve"
}

# Main script logic
main() {
    # Check if we're in the right directory
    if [ ! -d "$DOCS_SRC_DIR" ]; then
        print_error "Documentation directory '$DOCS_SRC_DIR' not found"
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Override defaults with environment variables
    if [ -n "$DOCS_PORT" ]; then
        PORT="$DOCS_PORT"
    fi
    
    if [ -n "$DOCS_HOST" ]; then
        HOST="$DOCS_HOST"
    fi
    
    # Parse command line arguments
    case "${1:-serve}" in
        "setup")
            setup_environment
            ;;
        "build")
            check_dependencies
            install_dependencies
            build_docs
            validate_build
            ;;
        "serve")
            check_dependencies
            install_dependencies
            build_docs
            validate_build
            serve_docs
            ;;
        "validate")
            validate_build
            ;;
        "clean")
            clean_build
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Trap Ctrl+C and cleanup
trap 'print_status "Stopping..."; exit 0' INT

# Run main function
main "$@" 