#!/bin/bash

# Global variables
declare -a PORTS=()
declare -a INSTANCE_PIDS=()
declare -a FAILED_PORTS=()
HEADLESS=false
FAST=false
FORCE_KILL=true
KILL_ONLY=false
STATUS_ONLY=false

# Platform detection
case "$OSTYPE" in
darwin*)
	PLATFORM="macos"
	;;
linux-gnu*)
	PLATFORM="linux"
	;;
*)
	echo "Error: Unsupported platform: $OSTYPE" >&2
	echo "Supported platforms: macOS, Linux" >&2
	exit 1
	;;
esac

# Usage function
show_usage() {
	cat <<EOF
Usage: $0 [OPTIONS]
       $0 -p PORT [OPTIONS]
       $0 --kill
       $0 --status

Options:
  -p, --port PORT  Specify port for Balatro instance (can be used multiple times)
                   Default: 12346 if no port specified
  --headless       Enable headless mode (sets BALATROBOT_HEADLESS=1)
  --fast           Enable fast mode (sets BALATROBOT_FAST=1)
  --kill           Kill all running Balatro instances and exit
  --status         Show information about running Balatro instances
  -h, --help       Show this help message

Examples:
  $0                            # Start single instance on default port 12346
  $0 -p 12347                   # Start single instance on port 12347
  $0 -p 12346 -p 12347          # Start two instances on ports 12346 and 12347
  $0 --headless --fast          # Start with headless and fast mode on default port
  $0 --kill                     # Kill all running Balatro instances
  $0 --status                   # Show running instances

EOF
}

# Parse command line arguments
parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case $1 in
		-p | --port)
			if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
				echo "Error: --port requires a port number" >&2
				exit 1
			fi
			if ! [[ "$2" =~ ^[0-9]+$ ]] || [[ "$2" -lt 1024 ]] || [[ "$2" -gt 65535 ]]; then
				echo "Error: Port must be a number between 1024 and 65535" >&2
				exit 1
			fi
			PORTS+=("$2")
			shift 2
			;;
		--headless)
			HEADLESS=true
			shift
			;;
		--fast)
			FAST=true
			shift
			;;
		--kill)
			KILL_ONLY=true
			shift
			;;
		--status)
			STATUS_ONLY=true
			shift
			;;
		-h | --help)
			show_usage
			exit 0
			;;
		*)
			echo "Error: Unknown option $1" >&2
			show_usage
			exit 1
			;;
		esac
	done

	# Validate arguments based on mode
	if [[ "$KILL_ONLY" == "true" ]]; then
		# In kill mode, no ports are required
		if [[ ${#PORTS[@]} -gt 0 ]]; then
			echo "Error: --kill cannot be used with port specifications" >&2
			show_usage
			exit 1
		fi
	elif [[ "$STATUS_ONLY" == "true" ]]; then
		# In status mode, no ports are required
		if [[ ${#PORTS[@]} -gt 0 ]]; then
			echo "Error: --status cannot be used with port specifications" >&2
			show_usage
			exit 1
		fi
	else
		# In normal mode, use default port 12346 if no port is specified
		if [[ ${#PORTS[@]} -eq 0 ]]; then
			PORTS=(12346)
		fi
	fi

	# Remove duplicates from ports array
	local unique_ports=()
	for port in "${PORTS[@]}"; do
		if [[ ! " ${unique_ports[*]} " =~ " ${port} " ]]; then
			unique_ports+=("$port")
		fi
	done
	PORTS=("${unique_ports[@]}")
}

# Check if a port is available
check_port_availability() {
	local port=$1

	# Check if port is in use
	if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
		if [[ "$FORCE_KILL" == "true" ]]; then
			lsof -ti:"$port" | xargs kill -9 2>/dev/null
			sleep 1

			# Verify port is now free
			if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
				echo "Error: Could not free port $port" >&2
				return 1
			fi
		else
			return 1
		fi
	fi
	return 0
}

# Get platform-specific configuration
get_platform_config() {
	case "$PLATFORM" in
	macos)
		# macOS Steam path and configuration
		STEAM_PATH="/Users/$USER/Library/Application Support/Steam/steamapps/common/Balatro"
		LIBRARY_ENV_VAR="DYLD_INSERT_LIBRARIES"
		LIBRARY_FILE="liblovely.dylib"
		BALATRO_EXECUTABLE="Balatro.app/Contents/MacOS/love"
		PROCESS_PATTERNS=("Balatro\.app" "balatro\.sh")
		;;
	linux)
		# Linux configuration using Proton (Steam Play)
		PREFIX="$HOME/.steam/steam/steamapps/compatdata/2379780"
		PROTON_DIR="$HOME/.steam/steam/steamapps/common/Proton 9.0 (Beta)"
		EXE="$HOME/.steam/debian-installation/steamapps/common/Balatro/Balatro.exe"

		STEAM_PATH="$PROTON_DIR"
		LIBRARY_ENV_VAR="" # Not used on Linux when running via Proton
		LIBRARY_FILE=""
		BALATRO_EXECUTABLE="proton"
		# Patterns of processes that should be terminated when cleaning up existing Balatro instances.
		# Do NOT include "balatro\.sh" – it would match this launcher script and terminate it.
		PROCESS_PATTERNS=("Balatro\.exe" "proton")
		;;
	*)
		echo "Error: Unsupported platform configuration" >&2
		exit 1
		;;
	esac
}

# Create logs directory
create_logs_directory() {
	if [[ ! -d "logs" ]]; then
		mkdir -p logs
		if [[ $? -ne 0 ]]; then
			echo "Error: Could not create logs directory" >&2
			return 1
		fi
	fi
	return 0
}

# Kill existing Balatro processes
kill_existing_processes() {
	# Build platform-specific grep pattern
	local grep_pattern=""
	for i in "${!PROCESS_PATTERNS[@]}"; do
		if [[ $i -eq 0 ]]; then
			grep_pattern="${PROCESS_PATTERNS[$i]}"
		else
			grep_pattern="$grep_pattern|${PROCESS_PATTERNS[$i]}"
		fi
	done

	if ps aux | grep -E "($grep_pattern)" | grep -v grep >/dev/null; then
		# Kill processes using platform-specific patterns
		for pattern in "${PROCESS_PATTERNS[@]}"; do
			pkill -f "$pattern" 2>/dev/null
		done
		sleep 2

		# Force kill if still running
		if ps aux | grep -E "($grep_pattern)" | grep -v grep >/dev/null; then
			for pattern in "${PROCESS_PATTERNS[@]}"; do
				pkill -9 -f "$pattern" 2>/dev/null
			done
			sleep 1
		fi
	fi
}

# Start a single Balatro instance
start_balatro_instance() {
	local port=$1
	local log_file="logs/balatro_${port}.log"

	# Remove old log file for this port
	if [[ -f "$log_file" ]]; then
		rm "$log_file"
	fi

	# Set environment variables
	export BALATROBOT_PORT="$port"
	if [[ "$HEADLESS" == "true" ]]; then
		export BALATROBOT_HEADLESS=1
	fi
	if [[ "$FAST" == "true" ]]; then
		export BALATROBOT_FAST=1
	fi

	# Set up platform-specific Balatro configuration
	# Platform-specific launch
	if [[ "$PLATFORM" == "linux" ]]; then
		PREFIX="$HOME/.steam/steam/steamapps/compatdata/2379780"
		PROTON_DIR="$STEAM_PATH"
		EXE="$HOME/.steam/debian-installation/steamapps/common/Balatro/Balatro.exe"

		# Steam / Proton context
		export STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/steam"
		export STEAM_COMPAT_DATA_PATH="$PREFIX"
		export SteamAppId=2379780
		export SteamGameId=2379780
		export WINEPREFIX="$PREFIX/pfx"

		# load Lovely/SteamModded
		export WINEDLLOVERRIDES="version=n,b"

		# Run via Proton
		(cd "$WINEPREFIX" && "$PROTON_DIR/proton" run "$EXE") >"$log_file" 2>&1 &
		local pid=$!
	else
		export ${LIBRARY_ENV_VAR}="${STEAM_PATH}/${LIBRARY_FILE}"
		"${STEAM_PATH}/${BALATRO_EXECUTABLE}" >"$log_file" 2>&1 &
		local pid=$!
	fi

	# Verify process started
	sleep 2
	if ! ps -p $pid >/dev/null; then
		echo "ERROR: Balatro instance failed to start on port $port. Check $log_file for details." >&2
		FAILED_PORTS+=("$port")
		return 1
	fi

	INSTANCE_PIDS+=("$pid")
	return 0
}

# Print information about running instances
print_instance_info() {
	local success_count=0

	for i in "${!PORTS[@]}"; do
		local port=${PORTS[$i]}
		local log_file="logs/balatro_${port}.log"

		if [[ " ${FAILED_PORTS[*]} " =~ " ${port} " ]]; then
			echo "• Port $port, FAILED, Log: $log_file"
		else
			local pid=${INSTANCE_PIDS[$success_count]}
			echo "• Port $port, PID $pid, Log: $log_file"
			((success_count++))
		fi
	done
}

# Show status of running Balatro instances
show_status() {
	# Build platform-specific grep pattern
	local grep_pattern=""
	for i in "${!PROCESS_PATTERNS[@]}"; do
		if [[ $i -eq 0 ]]; then
			grep_pattern="${PROCESS_PATTERNS[$i]}"
		else
			grep_pattern="$grep_pattern|${PROCESS_PATTERNS[$i]}"
		fi
	done

	# Find running Balatro processes
	local running_processes=()
	while IFS= read -r line; do
		running_processes+=("$line")
	done < <(ps aux | grep -E "($grep_pattern)" | grep -v grep | awk '{print $2}')

	if [[ ${#running_processes[@]} -eq 0 ]]; then
		echo "No Balatro instances are currently running"
		return 0
	fi

	# For each running process, find its listening port
	for pid in "${running_processes[@]}"; do
		local port=""
		local log_file=""

		# Use lsof to find listening ports for this PID
		if command -v lsof >/dev/null 2>&1; then
			# Look for TCP listening ports (any port >=1024, matching script validation)
			local ports_output
			ports_output=$(lsof -Pan -p "$pid" -i TCP 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2)

			# Find the first valid port for this Balatro instance
			while IFS= read -r found_port; do
				if [[ "$found_port" =~ ^[0-9]+$ ]] && [[ "$found_port" -ge 1024 ]] && [[ "$found_port" -le 65535 ]]; then
					port="$found_port"
					log_file="logs/balatro_${port}.log"
					break
				fi
			done <<<"$ports_output"
		fi

		# Only display processes that have a listening port (actual Balatro instances)
		if [[ -n "$port" ]]; then
			echo "• Port $port, PID $pid, Log: $log_file"
		fi
		# Skip processes without listening ports - they're not actual Balatro instances
	done
}

# Cleanup function for signal handling
cleanup() {
	echo ""
	echo "Script interrupted. Cleaning up..."
	if [[ ${#INSTANCE_PIDS[@]} -gt 0 ]]; then
		echo "Killing running Balatro instances..."
		for pid in "${INSTANCE_PIDS[@]}"; do
			kill "$pid" 2>/dev/null
		done
	fi
	exit 1
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM

# Main execution
main() {
	# Get platform configuration
	get_platform_config

	# Parse arguments
	parse_arguments "$@"

	# Handle kill-only mode
	if [[ "$KILL_ONLY" == "true" ]]; then
		echo "Killing all running Balatro instances..."
		kill_existing_processes
		echo "All Balatro instances have been terminated."
		exit 0
	fi

	# Handle status-only mode
	if [[ "$STATUS_ONLY" == "true" ]]; then
		show_status
		exit 0
	fi

	# Create logs directory
	if ! create_logs_directory; then
		exit 1
	fi

	# Kill existing processes
	kill_existing_processes

	# Check port availability and start instances
	local failed_count=0
	for port in "${PORTS[@]}"; do
		if ! check_port_availability "$port"; then
			echo "Error: Port $port is not available" >&2
			FAILED_PORTS+=("$port")
			((failed_count++))
			continue
		fi

		if ! start_balatro_instance "$port"; then
			((failed_count++))
			continue
		fi

	done

	# Print final status
	print_instance_info

	# Determine exit code
	local success_count=$((${#PORTS[@]} - failed_count))
	if [[ $failed_count -eq 0 ]]; then
		exit 0
	elif [[ $success_count -eq 0 ]]; then
		exit 3
	else
		exit 4
	fi
}

# Run main function with all arguments
main "$@"
