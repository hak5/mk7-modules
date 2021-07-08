import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';

@Component({
    selector: 'lib-sslsplit',
    templateUrl: './sslsplit.component.html',
    styleUrls: ['./sslsplit.component.css']
})
export class sslsplitComponent implements OnInit {

    constructor(private API: ApiService) { }

    poll_interval = null;
    poll_job(action: string, job_id: string): void {
        this.poll_interval = setInterval(
            () => {
                this.API.request(
                    {
                        module: 'sslsplit',
                        action: action,
                        job_id: job_id
                    },
                    (response) => {
                        if (response.is_complete) {
                            if (action === 'poll_dependencies') {
                                this.check_dependencies();
                            } else if (action === 'poll_certificate') {
                                this.check_certificate();
                            }
                            clearInterval(this.poll_interval);
                        }
                    }
                )
            }, 5000
        )
    }

    network_connected : boolean = null;
    network_status : boolean = false;
    check_network(): void {
        this.API.APIGet(
            '/api/settings/networking/clientmode/status',
            (response) => {
                this.network_connected = response.connected;
                if (response.connected) {
                    this.network_status = !this.network_status;
                }
            }
        )
    }

    dependency_sslsplit : boolean = null;
    check_dependencies(): void {
        this.API.request(
            {
                module: 'sslsplit',
                action: 'check_dependencies'
            },
            (response) => {
                this.dependency_sslsplit = response.dependency_sslsplit;
            }
        )
    }

    dependencies_status : boolean = true;
    install_dependencies(): void {
        this.dependencies_status = !this.dependencies_status;
        this.API.request(
            {
                module: 'sslsplit',
                action: 'install_dependencies'
            },
            (response) => {
                this.poll_job('poll_dependencies', response.job_id);
            }
        )
    }

    certificate_sslsplit : boolean = null;
    check_certificate(): void {
        this.API.request(
            {
                module: 'sslsplit',
                action: 'check_certificate'
            },
            (response) => {
                this.certificate_sslsplit = response.certificate_sslsplit;
            }
        )
    }

    certificate_status : boolean = true;
    generate_certificate(): void {
        this.certificate_status = !this.certificate_status;
        this.API.request(
            {
                module: 'sslsplit',
                action: 'generate_certificate'
            },
            (response) => {
                this.poll_job('poll_certificate', response.job_id);
            }
        )        
    }

    ngOnInit() {
        this.check_network();
        this.check_dependencies();
        this.check_certificate();
    }

    ngOnDestroy() {
        clearInterval(this.poll_interval);
    }

}